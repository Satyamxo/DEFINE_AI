from pathlib import Path

from app.parser.python_parser import parse_python_file
from app.parser.tree_sitter_parser import (
    detect_language,
    parse_tree_sitter_file,
)
from app.repository.scanner import scan_repository


TREE_SITTER_LANGUAGES = {
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
}


def analyze_repository(repository_path: str) -> dict:
    """
    Analyze supported source files in a repository.

    Python files use the existing Python AST parser.
    JavaScript and TypeScript files use Tree-sitter.

    Unsupported file types remain in the scan results but are
    not passed to a language-specific parser.
    """

    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository does not exist: {repository_path}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repository_path}"
        )

    scan_result = scan_repository(str(root))

    analyzed_files = []

    for file_info in scan_result["files"]:
        file_path = root / file_info["path"]

        # Prevent repository-relative paths from escaping the root.
        resolved_path = file_path.resolve()

        try:
            resolved_path.relative_to(root.resolve())
        except ValueError:
            continue

        if not resolved_path.is_file():
            continue

        extension = resolved_path.suffix.lower()

        # Keep the existing Python parser unchanged.
        if extension == ".py":
            parsed_data = parse_python_file(
                str(resolved_path)
            )

        # Use Tree-sitter for JavaScript and TypeScript.
        elif extension in TREE_SITTER_LANGUAGES:
            language = detect_language(str(resolved_path))

            if language is None:
                continue

            parsed_data = parse_tree_sitter_file(
                str(resolved_path),
                language,
            )

        # Preserve scanned files even when their parser isn't supported.
        else:
            parsed_data = {
                "language": file_info.get("language", "unknown"),
                "imports": [],
                "classes": [],
                "functions": [],
                "parsing_supported": False,
            }

        analyzed_files.append(
            {
                **file_info,
                "analysis": parsed_data,
            }
        )

    return {
        "repository": root.name,
        "total_files": len(analyzed_files),
        "files": analyzed_files,
    }