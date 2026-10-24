from pathlib import Path

from app.analyzer.repository_analyzer import analyze_repository
from app.rag.chunker import create_code_chunks
from app.rag.embedder import embed_code_chunks
from app.rag.vector_store import save_vector_index


def build_repository_index(
    repository_path: str,
    repository_analysis: dict | None = None,
    verbose: bool = False,
) -> dict:
    """
    Build and save the RAG index for a repository.

    If repository_analysis is provided, reuse it instead of
    analyzing the repository again.
    """

    root = Path(repository_path).resolve()

    if not root.is_dir():
        raise FileNotFoundError(
            f"Repository directory not found: {root}"
        )

    def log(message: str) -> None:
        if verbose:
            print(message)

    # --------------------------------------------------
    # 1. Analyze repository
    # --------------------------------------------------

    log("[1/4] Analyzing repository...")

    if repository_analysis is None:
        repository_analysis = analyze_repository(str(root))

    repository_name = repository_analysis.get(
        "repository",
        root.name,
    )

    total_files = repository_analysis.get("total_files", 0)

    log(f"Repository: {repository_name}")
    log(f"Files analyzed: {total_files}")

    # --------------------------------------------------
    # 2. Create code chunks
    # --------------------------------------------------

    log("[2/4] Creating code chunks...")

    chunks = create_code_chunks(
        repository_analysis=repository_analysis,
        repository_root=str(root),
        max_chunk_lines=80,
        overlap_lines=15,
    )

    if not chunks:
        raise ValueError(
            "No code chunks were generated. "
            "Check the repository and parser output."
        )

    log(f"Total chunks: {len(chunks)}")

    # --------------------------------------------------
    # 3. Generate embeddings
    # --------------------------------------------------

    log("[3/4] Generating embeddings...")

    embeddings = embed_code_chunks(
        chunks,
        batch_size=32,
    )

    log(f"Embedding matrix shape: {embeddings.shape}")

    # --------------------------------------------------
    # 4. Save vector index
    # --------------------------------------------------

    log("[4/4] Saving vector index...")

    index_directory = save_vector_index(
        repository_root=str(root),
        chunks=chunks,
        embeddings=embeddings,
    )

    result = {
        "status": "ready",
        "repository": repository_name,
        "repository_path": str(root),
        "total_files": total_files,
        "total_chunks": len(chunks),
        "embedding_dimensions": int(embeddings.shape[1]),
        "index_location": str(index_directory),
    }

    log("INDEXING COMPLETED")
    log(f"Index location: {index_directory}")

    return result