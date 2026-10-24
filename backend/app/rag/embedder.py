from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.

    The model runs locally after its initial download.
    """

    return SentenceTransformer(MODEL_NAME)


def build_embedding_text(chunk: dict) -> str:
    """
    Build a searchable representation of a code chunk.

    We include metadata alongside the code so the embedding
    can incorporate the symbol name and source location.
    """

    return (
        f"Repository: {chunk.get('repository', '')}\n"
        f"File: {chunk.get('file_path', '')}\n"
        f"Symbol: {chunk.get('symbol_name', '')}\n"
        f"Symbol type: {chunk.get('symbol_type', '')}\n"
        f"Code:\n{chunk.get('code', '')}"
    )


def embed_code_chunks(
    chunks: list[dict],
    batch_size: int = 32,
):
    """
    Generate normalized embeddings for code chunks.

    Returns a NumPy array with shape:

        (number_of_chunks, embedding_dimension)
    """

    if not chunks:
        raise ValueError(
            "Cannot generate embeddings for an empty chunk list."
        )

    model = get_embedding_model()

    texts = [
        build_embedding_text(chunk)
        for chunk in chunks
    ]

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embeddings


def embed_query(query: str):
    """
    Generate an embedding for a user's question.
    """

    if not query or not query.strip():
        raise ValueError(
            "The search query cannot be empty."
        )

    model = get_embedding_model()

    embedding = model.encode(
        [query.strip()],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embedding[0]