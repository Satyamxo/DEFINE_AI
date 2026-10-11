from pathlib import Path


# =========================================================
# PYTHON DEPENDENCY RESOLUTION
# =========================================================

def module_to_file(
    module_name: str,
    repository_root: Path,
) -> Path | None:
    """
    Resolve a Python module name to a local repository file.

    Example:
        core.extractor -> core/extractor.py
    """

    module_path = Path(*module_name.split("."))

    # Case 1: module.py
    file_path = repository_root / f"{module_path}.py"

    if file_path.is_file():
        return file_path

    # Case 2: module/__init__.py
    package_path = repository_root / module_path / "__init__.py"

    if package_path.is_file():
        return package_path

    return None


# =========================================================
# JAVASCRIPT / TYPESCRIPT DEPENDENCY RESOLUTION
# =========================================================

JS_TS_EXTENSIONS = (
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
)


def resolve_javascript_module(
    module_name: str,
    current_file: Path,
    repository_root: Path,
) -> Path | None:
    """
    Resolve a relative JavaScript/TypeScript module import.

    Examples:
        ./utils/helper.js
        ../components/Button
        ./services/api

    External packages such as 'react' are intentionally
    excluded from local dependency resolution.
    """

    if not module_name:
        return None

    # Initially support relative imports only.
    # Examples: ./helper and ../components/Button
    if not module_name.startswith(("./", "../")):
        return None

    target_base = (
        current_file.parent / module_name
    ).resolve()

    repository_root = repository_root.resolve()

    # Prevent imports from escaping the repository.
    try:
        target_base.relative_to(repository_root)
    except ValueError:
        return None

    candidates = []

    # Case 1: Explicit file path.
    if target_base.suffix:
        candidates.append(target_base)

    else:
        # Case 2: Extension omitted.
        for extension in JS_TS_EXTENSIONS:
            candidates.append(
                target_base.with_suffix(extension)
            )

        # Case 3: Directory import.
        for extension in JS_TS_EXTENSIONS:
            candidates.append(
                target_base / f"index{extension}"
            )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return None


# =========================================================
# SHARED DEPENDENCY RESOLUTION
# =========================================================

def resolve_file_dependencies(
    file_info: dict,
    repository_root: Path,
) -> list[dict]:
    """
    Resolve local dependencies for a single repository file.

    Python files use the existing Python import resolver.

    JavaScript and TypeScript files use relative module
    resolution.
    """

    dependencies = []

    relative_path = Path(file_info["path"])

    current_file = (
        repository_root / relative_path
    ).resolve()

    try:
        current_file.relative_to(repository_root.resolve())
    except ValueError:
        return dependencies

    analysis = file_info.get("analysis", {})

    imports = analysis.get("imports", [])

    extension = current_file.suffix.lower()

    for import_info in imports:

        target_file = None

        # ---------------------------------------------
        # Python imports
        # ---------------------------------------------

        if extension == ".py":

            import_type = import_info.get("type")

            if import_type == "import":
                module_name = import_info.get("name", "")

            elif import_type == "from_import":
                module_name = import_info.get("module", "")

            else:
                continue

            if not module_name:
                continue

            target_file = module_to_file(
                module_name,
                repository_root,
            )

        # ---------------------------------------------
        # JavaScript / TypeScript imports
        # ---------------------------------------------

        elif extension in JS_TS_EXTENSIONS:

            if import_info.get("type") != "module_import":
                continue

            module_name = import_info.get("module")

            target_file = resolve_javascript_module(
                module_name=module_name,
                current_file=current_file,
                repository_root=repository_root,
            )

        # ---------------------------------------------
        # Skip unsupported file types
        # ---------------------------------------------

        else:
            continue

        if target_file is None:
            continue

        target_file = target_file.resolve()

        # Avoid self-dependencies.
        if target_file == current_file:
            continue

        try:
            source_relative = current_file.relative_to(
                repository_root.resolve()
            ).as_posix()

            target_relative = target_file.relative_to(
                repository_root.resolve()
            ).as_posix()

        except ValueError:
            continue

        dependencies.append(
            {
                "source": source_relative,
                "target": target_relative,
                "type": "IMPORTS",
            }
        )

    return dependencies


# =========================================================
# REPOSITORY DEPENDENCY GRAPH
# =========================================================

def build_dependency_graph_data(
    repository_analysis: dict,
    repository_root: str,
) -> dict:
    """
    Build repository-level dependency relationships
    across supported languages.
    """

    root = Path(repository_root).resolve()

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository does not exist: {repository_root}"
        )

    dependencies = []

    for file_info in repository_analysis["files"]:

        file_dependencies = resolve_file_dependencies(
            file_info,
            root,
        )

        dependencies.extend(file_dependencies)

    return {
        "repository": repository_analysis["repository"],
        "dependencies": dependencies,
    }