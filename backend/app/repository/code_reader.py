from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def read_repository_file(
    repository_root: Path,
    relative_path: str,
) -> dict:

    relative_path = Path(relative_path)

    # Prevent paths such as:
    # ../../something
    if relative_path.is_absolute():
        raise ValueError("Absolute paths are not allowed.")

    if ".." in relative_path.parts:
        raise ValueError("Path traversal is not allowed.")

    file_path = repository_root / relative_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {relative_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Path is not a file: {relative_path}"
        )

    # Make sure the resolved file is actually
    # inside the repository.
    repository_root = repository_root.resolve()
    file_path = file_path.resolve()

    try:
        file_path.relative_to(repository_root)
    except ValueError:
        raise ValueError(
            "Requested file is outside repository."
        )

    source = file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    lines = source.splitlines()

    return {
        "path": relative_path.as_posix(),
        "content": source,
        "line_count": len(lines),
    }