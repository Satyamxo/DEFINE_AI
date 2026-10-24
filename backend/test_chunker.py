import json
import sys
from pathlib import Path

from app.analyzer.repository_analyzer import analyze_repository
from app.rag.chunker import create_code_chunks


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python test_chunker.py <repository_path>"
        )
        raise SystemExit(1)

    repository_path = Path(
        sys.argv[1]
    ).resolve()

    if not repository_path.is_dir():
        print(
            f"Repository directory not found: {repository_path}"
        )
        raise SystemExit(1)

    print("Analyzing repository...")
    print(f"Path: {repository_path}")

    repository_analysis = analyze_repository(
        str(repository_path)
    )

    print("Creating code chunks...")

    chunks = create_code_chunks(
        repository_analysis=repository_analysis,
        repository_root=str(repository_path),
        max_chunk_lines=80,
        overlap_lines=15,
    )

    print()
    print("========== CHUNKING RESULTS ==========")
    print(
        "Repository:",
        repository_analysis.get("repository"),
    )
    print(
        "Files analyzed:",
        repository_analysis.get("total_files"),
    )
    print(
        "Total chunks:",
        len(chunks),
    )

    if not chunks:
        print(
            "No chunks were generated. "
            "Check whether the repository contains readable files."
        )
        raise SystemExit(1)

    print()
    print("========== FIRST THREE CHUNKS ==========")

    for chunk in chunks[:3]:
        preview = {
            "chunk_id": chunk["chunk_id"],
            "file_path": chunk["file_path"],
            "symbol_name": chunk["symbol_name"],
            "symbol_type": chunk["symbol_type"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "chunking_strategy": chunk["chunking_strategy"],
            "code_preview": chunk["code"][:500],
        }

        print(
            json.dumps(
                preview,
                indent=2,
                ensure_ascii=False,
            )
        )

    output_path = Path(
        "code_chunks.json"
    ).resolve()

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            chunks,
            output_file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(f"Saved chunks to: {output_path}")


if __name__ == "__main__":
    main()