import hashlib
import json
import re
from pathlib import Path

import numpy as np


BACKEND_ROOT = Path(__file__).resolve().parents[2]

INDEX_ROOT = BACKEND_ROOT / "data" / "rag_indexes"


def _get_index_directory(repository_root: str) -> Path:
    """
    Generate a stable local index directory for a repository path.
    """

    resolved_path = str(
        Path(repository_root).resolve()
    )

    repository_name = Path(
        resolved_path
    ).name

    safe_name = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        repository_name,
    )

    path_hash = hashlib.sha256(
        resolved_path.encode("utf-8")
    ).hexdigest()[:12]

    return INDEX_ROOT / f"{safe_name}_{path_hash}"


def save_vector_index(
    repository_root: str,
    chunks: list[dict],
    embeddings: np.ndarray,
) -> Path:
    """
    Save code chunks and their embeddings to disk.
    """

    if len(chunks) == 0:
        raise ValueError(
            "Cannot save an empty vector index."
        )

    if embeddings.ndim != 2:
        raise ValueError(
            "Embeddings must be a two-dimensional array."
        )

    if len(chunks) != embeddings.shape[0]:
        raise ValueError(
            "Number of chunks does not match number of embeddings."
        )

    index_directory = _get_index_directory(
        repository_root
    )

    index_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path = index_directory / "chunks.json"
    embeddings_path = index_directory / "embeddings.npy"
    manifest_path = index_directory / "manifest.json"

    # Save chunk metadata and source code.
    with metadata_path.open(
        "w",
        encoding="utf-8",
    ) as metadata_file:
        json.dump(
            chunks,
            metadata_file,
            ensure_ascii=False,
            indent=2,
        )

    # Save vectors as a NumPy array.
    np.save(
        embeddings_path,
        embeddings.astype(np.float32),
    )

    manifest = {
        "repository_root": str(
            Path(repository_root).resolve()
        ),
        "chunk_count": len(chunks),
        "embedding_dimension": int(
            embeddings.shape[1]
        ),
        "model_name": (
            "sentence-transformers/all-MiniLM-L6-v2"
        ),
    }

    with manifest_path.open(
        "w",
        encoding="utf-8",
    ) as manifest_file:
        json.dump(
            manifest,
            manifest_file,
            indent=2,
        )

    return index_directory


def load_vector_index(
    repository_root: str,
) -> tuple[list[dict], np.ndarray]:
    """
    Load chunks and embeddings for a repository.
    """

    index_directory = _get_index_directory(
        repository_root
    )

    metadata_path = index_directory / "chunks.json"
    embeddings_path = index_directory / "embeddings.npy"
    manifest_path = index_directory / "manifest.json"

    if not (
        metadata_path.exists()
        and embeddings_path.exists()
        and manifest_path.exists()
    ):
        raise FileNotFoundError(
            "Vector index not found. "
            "Build the index before searching."
        )

    with manifest_path.open(
        "r",
        encoding="utf-8",
    ) as manifest_file:
        manifest = json.load(manifest_file)

    expected_root = str(
        Path(repository_root).resolve()
    )

    if manifest.get("repository_root") != expected_root:
        raise ValueError(
            "The saved index belongs to a different repository path."
        )

    with metadata_path.open(
        "r",
        encoding="utf-8",
    ) as metadata_file:
        chunks = json.load(metadata_file)

    embeddings = np.load(
        embeddings_path,
        allow_pickle=False,
    )

    if embeddings.ndim != 2:
        raise ValueError(
            "Stored embeddings have an invalid shape."
        )

    if len(chunks) != embeddings.shape[0]:
        raise ValueError(
            "Stored chunk count does not match embedding count."
        )

    if manifest.get("chunk_count") != len(chunks):
        raise ValueError(
            "Index manifest does not match stored chunks."
        )

    if (
        manifest.get("embedding_dimension")
        != embeddings.shape[1]
    ):
        raise ValueError(
            "Index embedding dimension is inconsistent."
        )

    return chunks, embeddings