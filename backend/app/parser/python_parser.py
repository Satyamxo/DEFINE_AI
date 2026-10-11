import ast
from pathlib import Path


def parse_python_file(file_path: str) -> dict:
    """
    Parse a Python file and extract:
    - imports
    - classes
    - functions
    - methods
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    source_code = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    try:
        tree = ast.parse(source_code)
    except SyntaxError as error:
        return {
            "file": str(path),
            "error": f"Syntax error: {error}",
        }

    result = {
        "file": str(path),
        "imports": [],
        "classes": [],
        "functions": [],
    }

    for node in ast.iter_child_nodes(tree):

        # -------------------------
        # Imports
        # -------------------------

        if isinstance(node, ast.Import):

            for alias in node.names:
                result["imports"].append({
                    "type": "import",
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                })

        elif isinstance(node, ast.ImportFrom):

            module = node.module or ""

            for alias in node.names:
                result["imports"].append({
                    "type": "from_import",
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                })

        # -------------------------
        # Classes
        # -------------------------

        elif isinstance(node, ast.ClassDef):

            class_info = {
                "name": node.name,
                "line_start": node.lineno,
                "line_end": getattr(
                    node,
                    "end_lineno",
                    node.lineno,
                ),
                "methods": [],
            }

            for child in node.body:

                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    class_info["methods"].append({
                        "name": child.name,
                        "line_start": child.lineno,
                        "line_end": getattr(
                            child,
                            "end_lineno",
                            child.lineno,
                        ),
                    })

            result["classes"].append(class_info)

        # -------------------------
        # Functions
        # -------------------------

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):

            result["functions"].append({
                "name": node.name, 
                "line_start": node.lineno,
                "line_end": getattr(
                    node,
                    "end_lineno",
                    node.lineno,
                ),
            })

    return result