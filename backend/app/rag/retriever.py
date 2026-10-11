import re
from collections import Counter

import numpy as np

from app.rag.embedder import embed_query
from app.rag.vector_store import load_vector_index


# Words that usually contribute little to code retrieval.
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "be", "been", "being", "do", "does", "did",
    "how", "what", "where", "when", "why", "who",
    "which", "this", "that", "these", "those",
    "and", "or", "but", "to", "of", "in", "on",
    "for", "from", "with", "by", "it", "its",
    "can", "could", "would", "should",
    "me", "my", "i", "we", "you", "they",
    "show", "find", "explain", "tell", "please",
}


def tokenize(text: str) -> list[str]:
    """
    Convert text into searchable tokens.

    Examples:
        process_input -> process_input, process, input
        buildRagChain -> buildRagChain, build, rag, chain
    """
    if not text:
        return []

    # Extract identifiers, words and numbers.
    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)

    tokens = []

    for token in raw_tokens:
        normalized = token.lower()

        if normalized not in STOP_WORDS:
            tokens.append(normalized)

        # Split snake_case identifiers.
        for part in token.split("_"):
            part = part.lower()

            if part and part not in STOP_WORDS:
                tokens.append(part)

        # Split camelCase identifiers.
        camel_parts = re.sub(
            r"([a-z0-9])([A-Z])",
            r"\1 \2",
            token,
        ).split()

        for part in camel_parts:
            part = part.lower()

            if part and part not in STOP_WORDS:
                tokens.append(part)

    return tokens


def build_searchable_text(chunk: dict) -> str:
    """
    Combine useful chunk metadata and source code
    into one searchable text representation.
    """
    return "\n".join(
        [
            str(chunk.get("repository", "")),
            str(chunk.get("file_path", "")),
            str(chunk.get("symbol_name", "")),
            str(chunk.get("symbol_type", "")),
            str(chunk.get("code", "")),
        ]
    )


def calculate_keyword_score(
    query_tokens: list[str],
    chunk: dict,
) -> float:
    """
    Calculate lexical relevance using query-token overlap.

    Matches in symbol names and file paths receive
    additional weight.
    """
    if not query_tokens:
        return 0.0

    symbol_name = str(chunk.get("symbol_name", ""))
    file_path = str(chunk.get("file_path", ""))

    symbol_tokens = set(tokenize(symbol_name))
    path_tokens = set(tokenize(file_path))
    code_tokens = Counter(
        tokenize(str(chunk.get("code", "")))
    )

    query_terms = set(query_tokens)

    total_score = 0.0

    for term in query_terms:
        if term in symbol_tokens:
            total_score += 3.0

        if term in path_tokens:
            total_score += 2.0

        if code_tokens[term] > 0:
            total_score += min(
                1.0 + 0.1 * (code_tokens[term] - 1),
                1.5,
            )

    # Normalize so longer queries do not automatically
    # receive higher scores.
    return total_score / len(query_terms)


def extract_code_identifiers(query: str) -> list[str]:
    """
    Extract likely code identifiers from a question.

    Prioritize identifiers such as:
        process_input
        buildRagChain
        load_vector_store
    """
    candidates = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_]*\b",
        query,
    )

    identifiers = []

    for candidate in candidates:
        has_underscore = "_" in candidate

        has_camel_case = bool(
            re.search(r"[a-z][A-Z]", candidate)
        )

        if has_underscore or has_camel_case:
            identifiers.append(candidate)

    return identifiers


def calculate_identifier_bonus(
    query: str,
    chunk: dict,
) -> float:
    """
    Give an additional boost when a chunk defines
    an identifier explicitly mentioned in the query.
    """
    identifiers = extract_code_identifiers(query)

    if not identifiers:
        return 0.0

    symbol_name = str(chunk.get("symbol_name", ""))
    code = str(chunk.get("code", ""))

    for identifier in identifiers:
        # Exact symbol-name match.
        if symbol_name == identifier:
            # Prefer the actual definition.
            definition_pattern = (
                rf"\bdef\s+{re.escape(identifier)}\s*\("
            )

            if re.search(definition_pattern, code):
                return 1.0

            # Still reward an exact symbol-name match.
            return 0.5

        # A smaller bonus for mentioning the identifier
        # in the source code.
        if re.search(
            rf"\b{re.escape(identifier)}\b",
            code,
        ):
            return 0.05

    return 0.0


def retrieve_relevant_chunks(
    query: str,
    repository_root: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve code using semantic search and keyword search.

    Ranking uses:
      1. Semantic rank.
      2. Keyword rank.
      3. Exact identifier matching.
    """
    if not query or not query.strip():
        raise ValueError("The search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Load the existing local vector index.
    chunks, embeddings = load_vector_index(repository_root)

    if not chunks:
        return []

    query = query.strip()

    # --------------------------------------------------
    # 1. Semantic retrieval
    # --------------------------------------------------

    query_embedding = embed_query(query)

    if embeddings.shape[1] != query_embedding.shape[0]:
        raise ValueError(
            "Query embedding dimension does not match "
            "the stored index. Rebuild the index using "
            "the same embedding model."
        )

    semantic_scores = embeddings @ query_embedding

    semantic_order = np.argsort(
        semantic_scores
    )[::-1]

    semantic_ranks = np.empty(
        len(chunks),
        dtype=int,
    )

    semantic_ranks[semantic_order] = np.arange(
        1,
        len(chunks) + 1,
    )

    # --------------------------------------------------
    # 2. Keyword retrieval
    # --------------------------------------------------

    query_tokens = tokenize(query)

    keyword_scores = np.array(
        [
            calculate_keyword_score(
                query_tokens,
                chunk,
            )
            for chunk in chunks
        ],
        dtype=float,
    )

    # Stable sorting makes equal-score ordering
    # deterministic for a fixed chunk list.
    keyword_order = np.argsort(
        -keyword_scores,
        kind="stable",
    )

    keyword_ranks = np.empty(
        len(chunks),
        dtype=int,
    )

    keyword_ranks[keyword_order] = np.arange(
        1,
        len(chunks) + 1,
    )

    # --------------------------------------------------
    # 3. Combine rankings using RRF
    # --------------------------------------------------

     # --------------------------------------------------
    # 3. Combine rankings using weighted RRF
    # --------------------------------------------------

    rrf_constant = 60

    # Semantic ranking is the primary signal.
    semantic_weight = 3.0

    # Keyword ranking provides supporting evidence.
    keyword_weight = 0.5

    results = []

    for index, chunk in enumerate(chunks):
        semantic_rank = int(semantic_ranks[index])
        keyword_rank = int(keyword_ranks[index])

        semantic_rrf = (
            semantic_weight
            / (rrf_constant + semantic_rank)
        )

        if keyword_scores[index] > 0:
            keyword_rrf = (
                keyword_weight
                / (rrf_constant + keyword_rank)
            )
        else:
            keyword_rrf = 0.0

        identifier_bonus = calculate_identifier_bonus(
            query,
            chunk,
        )

        hybrid_score = (
            semantic_rrf
            + keyword_rrf
            + identifier_bonus
        )

        result = dict(chunk)

        result["similarity_score"] = float(
            semantic_scores[index]
        )

        result["keyword_score"] = float(
            keyword_scores[index]
        )

        result["hybrid_score"] = float(
            hybrid_score
        )

        result["semantic_rank"] = semantic_rank
        result["keyword_rank"] = keyword_rank

        result["identifier_bonus"] = float(
            identifier_bonus
        )

        results.append(result)

    # --------------------------------------------------
    # 4. Final ranking
    # --------------------------------------------------

    results.sort(
        key=lambda item: (
            item["hybrid_score"],
            item["similarity_score"],
        ),
        reverse=True,
    )

    return results[:top_k]