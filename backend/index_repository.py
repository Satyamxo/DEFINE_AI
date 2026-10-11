
import sys
from pathlib import Path

from app.rag.indexer import build_repository_index


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python index_repository.py <repository_path>"
        )
        raise SystemExit(1)

    repository_path = Path(sys.argv[1]).resolve()

    if not repository_path.is_dir():
        print(
            f"Repository directory not found: {repository_path}"
        )
        raise SystemExit(1)

    print("=" * 60)
    print("DEFINE-AI: REPOSITORY INDEXING")
    print("=" * 60)

    try:
        result = build_repository_index(
            repository_path=str(repository_path),
            verbose=True,
        )

        print("\n" + "=" * 60)
        print("INDEXING COMPLETED")
        print("=" * 60)

        print(f"Repository: {result['repository_path']}")
        print(f"Chunks: {result['total_chunks']}")
        print(
            "Embedding dimensions: "
            f"{result['embedding_dimensions']}"
        )
        print(f"Index location: {result['index_location']}")

    except Exception as error:
        print(f"\nINDEXING FAILED: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()