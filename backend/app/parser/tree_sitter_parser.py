from pathlib import Path

import tree_sitter_javascript
import tree_sitter_typescript

from tree_sitter import Language, Parser


# =========================================================
# LANGUAGE CONFIGURATION
# =========================================================

LANGUAGE_CONFIG = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}


def get_tree_sitter_parser(language_name: str) -> Parser:
    """
    Create a Tree-sitter parser for a supported language.
    """

    if language_name == "javascript":
        language = Language(
            tree_sitter_javascript.language()
        )

    elif language_name == "typescript":
        language = Language(
            tree_sitter_typescript.language_typescript()
        )

    elif language_name == "tsx":
        language = Language(
            tree_sitter_typescript.language_tsx()
        )

    else:
        raise ValueError(
            f"Unsupported Tree-sitter language: {language_name}"
        )

    return Parser(language)


def detect_language(file_path: str | Path) -> str | None:
    """
    Detect the language using the file extension.

    Returns None for unsupported extensions.
    """

    extension = Path(file_path).suffix.lower()

    return LANGUAGE_CONFIG.get(extension)


# =========================================================
# TREE UTILITIES
# =========================================================

def get_node_text(
    node,
    source_bytes: bytes,
) -> str:
    """
    Extract source text represented by a syntax-tree node.
    """

    return source_bytes[
        node.start_byte:node.end_byte
    ].decode("utf-8", errors="replace")


def get_node_name(
    node,
    source_bytes: bytes,
) -> str | None:
    """
    Read a node's name field when available.
    """

    name_node = node.child_by_field_name("name")

    if name_node is None:
        return None

    return get_node_text(
        name_node,
        source_bytes,
    )


def get_line_range(node) -> tuple[int, int]:
    """
    Convert Tree-sitter's zero-based row positions
    into one-based source line numbers.
    """

    line_start = node.start_point.row + 1
    line_end = node.end_point.row + 1

    return line_start, line_end


# =========================================================
# IMPORT EXTRACTION
# =========================================================

def extract_imports(
    root_node,
    source_bytes: bytes,
) -> list[dict]:
    """
    Extract JavaScript and TypeScript import statements.

    Returns structured import information while preserving
    the original statement and its source line range.
    """

    imports = []

    def visit(node):
        if node.type == "import_statement":
            line_start, line_end = get_line_range(node)

            statement = get_node_text(
                node,
                source_bytes,
            )

            # The module specifier is normally a direct
            # string child of the import_statement node.
            module_name = None

            for child in node.named_children:
                if child.type == "string":
                    raw_module = get_node_text(
                        child,
                        source_bytes,
                    )

                    # Remove the surrounding quotes.
                    if len(raw_module) >= 2:
                        module_name = raw_module[1:-1]

                    break

            imports.append(
                {
                    "type": "module_import",
                    "module": module_name,
                    "statement": statement,
                    "line": line_start,
                    "line_start": line_start,
                    "line_end": line_end,
                }
            )

        for child in node.named_children:
            visit(child)

    visit(root_node)

    return imports


# =========================================================
# FUNCTION EXTRACTION
# =========================================================

FUNCTION_NODE_TYPES = {
    "function_declaration",
}


def extract_functions(
    root_node,
    source_bytes: bytes,
) -> list[dict]:
    """
    Extract named top-level function declarations
    and arrow functions assigned to top-level variables.

    Class methods are handled separately.
    """

    functions = []

    def add_function(name: str, node):
        line_start, line_end = get_line_range(node)

        functions.append(
            {
                "name": name,
                "line_start": line_start,
                "line_end": line_end,
            }
        )

    def visit(node, inside_function=False):
        # Named function declarations
        if node.type in FUNCTION_NODE_TYPES:
            name = get_node_name(
                node,
                source_bytes,
            )

            if name and not inside_function:
                add_function(name, node)

            # Do not classify nested functions as top-level.
            for child in node.named_children:
                visit(child, inside_function=True)

            return

        # Arrow functions assigned to variables:
        #
        # const processVideo = (url) => { ... }
        #
        # Tree-sitter represents this as a variable_declarator
        # containing an arrow_function.
        if (
            node.type == "variable_declarator"
            and not inside_function
        ):
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")

            if (
                name_node is not None
                and value_node is not None
                and value_node.type in {
                    "arrow_function",
                    "function_expression",
                }
            ):
                name = get_node_text(
                    name_node,
                    source_bytes,
                )

                add_function(name, node)

        for child in node.named_children:
            visit(child, inside_function)

    for child in root_node.named_children:
        visit(child)

    return functions


# =========================================================
# CLASS AND METHOD EXTRACTION
# =========================================================

CLASS_NODE_TYPES = {
    "class_declaration",
    "class",
}


def extract_classes(
    root_node,
    source_bytes: bytes,
) -> list[dict]:
    """
    Extract class declarations and their direct methods.
    """

    classes = []

    def extract_methods(class_node):
        methods = []

        body_node = class_node.child_by_field_name("body")

        if body_node is None:
            return methods

        for member in body_node.named_children:
            # Standard JavaScript/TypeScript class methods.
            if member.type != "method_definition":
                continue

            name_node = member.child_by_field_name("name")

            if name_node is None:
                continue

            method_name = get_node_text(
                name_node,
                source_bytes,
            )

            line_start, line_end = get_line_range(member)

            methods.append(
                {
                    "name": method_name,
                    "line_start": line_start,
                    "line_end": line_end,
                }
            )

        return methods

    def visit(node):
        if node.type in CLASS_NODE_TYPES:
            name = get_node_name(
                node,
                source_bytes,
            )

            if name:
                line_start, line_end = get_line_range(node)

                classes.append(
                    {
                        "name": name,
                        "line_start": line_start,
                        "line_end": line_end,
                        "methods": extract_methods(node),
                    }
                )

        for child in node.named_children:
            visit(child)

    visit(root_node)

    return classes


# =========================================================
# PUBLIC PARSER FUNCTION
# =========================================================

def parse_tree_sitter_file(
    file_path: str | Path,
    language_name: str | None = None,
) -> dict:
    """
    Parse a JavaScript, TypeScript, or TSX source file.

    This initial implementation extracts imports,
    classes, methods, and supported function declarations.
    """

    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    if language_name is None:
        language_name = detect_language(file_path)

    if language_name is None:
        raise ValueError(
            f"Unsupported source file: {file_path.suffix}"
        )

    parser = get_tree_sitter_parser(language_name)

    source_bytes = file_path.read_bytes()

    tree = parser.parse(source_bytes)

    root_node = tree.root_node

    imports = extract_imports(
        root_node,
        source_bytes,
    )

    classes = extract_classes(
        root_node,
        source_bytes,
    )

    functions = extract_functions(
        root_node,
        source_bytes,
    )

    return {
        "language": language_name,
        "imports": imports,
        "classes": classes,
        "functions": functions,
        "has_syntax_errors": root_node.has_error,
    }