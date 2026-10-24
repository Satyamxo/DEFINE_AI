
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

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}


def scan_repository(repository_path: str) -> dict:
    root = Path(repository_path)

    if not root.is_dir():
        raise FileNotFoundError(
            f"Repository does not exist: {repository_path}"
        )

    files = []

    for path in root.rglob("*"):
        relative_path = path.relative_to(root)

        # Ignore directories within the repository only
        if any(
            part in IGNORED_DIRECTORIES
            for part in relative_path.parts
        ):
            continue

        if not path.is_file():
            continue

        extension = path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        files.append({
            "path": relative_path.as_posix(),
            "name": path.name,
            "extension": extension,
            "language": SUPPORTED_EXTENSIONS[extension],
            "size": path.stat().st_size,
        })

    return {
        "repository": root.name,
        "total_files": len(files),
        "files": files,
    }