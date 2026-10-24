import hashlib
from pathlib import Path


DEFAULT_MAX_CHUNK_LINES = 80
DEFAULT_OVERLAP_LINES = 15


def _read_source_file(
    repository_root: Path,
    relative_path: str,
) -> list[str]:
    """
    Read a source file safely and return its lines.

    The file must be inside the repository root.
    """

    root = repository_root.resolve()

    candidate = (root / relative_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        raise ValueError(
            f"File is outside the repository: {relative_path}"
        )

    if not candidate.is_file():
        raise FileNotFoundError(
            f"Source file not found: {relative_path}"
        )

    try:
        with candidate.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as source_file:
            return source_file.readlines()

    except OSError as exc:
        raise OSError(
            f"Unable to read source file: {relative_path}"
        ) from exc


def _get_valid_line_range(
    symbol: dict,
    total_lines: int,
) -> tuple[int, int] | None:
    """
    Extract and validate a symbol's line range.

    Line numbers are 1-based.
    """

    start = symbol.get("line_start")
    end = symbol.get("line_end")

    if not isinstance(start, int) or not isinstance(end, int):
        return None

    if start < 1 or end < start:
        return None

    if start > total_lines:
        return None

    end = min(end, total_lines)

    return start, end


def _merge_ranges(
    ranges: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """
    Merge overlapping or adjacent line ranges.
    """

    if not ranges:
        return []

    sorted_ranges = sorted(ranges)

    merged = [sorted_ranges[0]]

    for start, end in sorted_ranges[1:]:
        previous_start, previous_end = merged[-1]

        if start <= previous_end + 1:
            merged[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged.append((start, end))

    return merged


def _find_uncovered_ranges(
    total_lines: int,
    covered_ranges: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """
    Find lines not covered by any recognized symbol.

    These regions can contain imports, constants, module-level
    configuration or code that the parser did not recognize.
    """

    if total_lines <= 0:
        return []

    merged = _merge_ranges(covered_ranges)

    uncovered = []
    current_line = 1

    for start, end in merged:
        if current_line < start:
            uncovered.append(
                (current_line, start - 1)
            )

        current_line = max(
            current_line,
            end + 1,
        )

    if current_line <= total_lines:
        uncovered.append(
            (current_line, total_lines)
        )

    return uncovered


def _split_range(
    start: int,
    end: int,
    max_chunk_lines: int,
    overlap_lines: int,
) -> list[tuple[int, int]]:
    """
    Split a range into bounded chunks.

    Long chunks overlap slightly so that code near a boundary
    retains some surrounding context.
    """

    if start > end:
        return []

    step = max_chunk_lines - overlap_lines

    ranges = []
    current_start = start

    while current_start <= end:
        current_end = min(
            current_start + max_chunk_lines - 1,
            end,
        )

        ranges.append(
            (current_start, current_end)
        )

        if current_end == end:
            break

        current_start += step

    return ranges


def _extract_code(
    source_lines: list[str],
    start_line: int,
    end_line: int,
) -> str:
    """
    Extract source code using 1-based inclusive line numbers.
    """

    return "".join(
        source_lines[start_line - 1:end_line]
    )


def _make_chunk_id(
    repository: str,
    file_path: str,
    symbol_type: str,
    symbol_name: str,
    start_line: int,
    end_line: int,
    code: str,
) -> str:
    """
    Generate a deterministic identifier for a code chunk.
    """

    identity = "\n".join(
        [
            repository,
            file_path,
            symbol_type,
            symbol_name,
            str(start_line),
            str(end_line),
            code,
        ]
    )

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()

    return digest


def _add_chunks_for_range(
    chunks: list[dict],
    repository: str,
    file_path: str,
    language: str,
    source_lines: list[str],
    symbol_type: str,
    symbol_name: str,
    start_line: int,
    end_line: int,
    max_chunk_lines: int,
    overlap_lines: int,
    strategy: str,
) -> None:
    """
    Split a symbol or code region into chunks and append them
    to the output collection.
    """

    ranges = _split_range(
        start=start_line,
        end=end_line,
        max_chunk_lines=max_chunk_lines,
        overlap_lines=overlap_lines,
    )

    for chunk_start, chunk_end in ranges:
        code = _extract_code(
            source_lines,
            chunk_start,
            chunk_end,
        )

        if not code.strip():
            continue

        chunk_id = _make_chunk_id(
            repository=repository,
            file_path=file_path,
            symbol_type=symbol_type,
            symbol_name=symbol_name,
            start_line=chunk_start,
            end_line=chunk_end,
            code=code,
        )

        chunks.append(
            {
                "chunk_id": chunk_id,
                "repository": repository,
                "file_path": file_path,
                "language": language,
                "symbol_name": symbol_name,
                "symbol_type": symbol_type,
                "start_line": chunk_start,
                "end_line": chunk_end,
                "code": code,
                "chunking_strategy": strategy,
            }
        )


def create_code_chunks(
    repository_analysis: dict,
    repository_root: str,
    max_chunk_lines: int = DEFAULT_MAX_CHUNK_LINES,
    overlap_lines: int = DEFAULT_OVERLAP_LINES,
) -> list[dict]:
    """
    Convert repository analysis into searchable code chunks.

    Strategy:
    1. Create chunks for classes.
    2. Create chunks for methods.
    3. Create chunks for top-level functions.
    4. Split large symbols into overlapping chunks.
    5. Create fallback chunks for source regions not covered
       by recognized symbols.

    The function does not modify the original repository analysis.
    """

    if max_chunk_lines < 1:
        raise ValueError(
            "max_chunk_lines must be at least 1."
        )

    if overlap_lines < 0:
        raise ValueError(
            "overlap_lines cannot be negative."
        )

    if overlap_lines >= max_chunk_lines:
        raise ValueError(
            "overlap_lines must be smaller than max_chunk_lines."
        )

    root = Path(repository_root).resolve()

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(
            f"Repository directory does not exist: {root}"
        )

    repository_name = repository_analysis.get(
        "repository",
        root.name,
    )

    chunks = []

    for file_info in repository_analysis.get("files", []):
        relative_path = Path(
            file_info["path"]
        ).as_posix()

        try:
            source_lines = _read_source_file(
                root,
                relative_path,
            )

        except (OSError, ValueError) as exc:
            # Skip files that cannot safely be read.
            print(
                f"Skipping {relative_path}: {exc}"
            )
            continue

        total_lines = len(source_lines)

        if total_lines == 0:
            continue

        analysis = file_info.get("analysis") or {}

        language = (
    file_info.get("language")
    or analysis.get("language")
    or {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
    }.get(Path(relative_path).suffix.lower(), "text")
)

        # Keep track of source lines covered by recognized symbols.
        covered_ranges = []

        # --------------------------------------------------
        # 1. Classes and methods
        # --------------------------------------------------

        for class_info in analysis.get("classes", []):
            class_range = _get_valid_line_range(
                class_info,
                total_lines,
            )

            if class_range is None:
                continue

            class_start, class_end = class_range

            covered_ranges.append(
                class_range
            )

            class_name = class_info.get(
                "name",
                "unknown_class",
            )

            _add_chunks_for_range(
                chunks=chunks,
                repository=repository_name,
                file_path=relative_path,
                language=language,
                source_lines=source_lines,
                symbol_type="class",
                symbol_name=class_name,
                start_line=class_start,
                end_line=class_end,
                max_chunk_lines=max_chunk_lines,
                overlap_lines=overlap_lines,
                strategy="symbol",
            )

            for method_info in class_info.get(
                "methods",
                [],
            ):
                method_range = _get_valid_line_range(
                    method_info,
                    total_lines,
                )

                if method_range is None:
                    continue

                method_start, method_end = method_range

                covered_ranges.append(
                    method_range
                )

                method_name = method_info.get(
                    "name",
                    "unknown_method",
                )

                _add_chunks_for_range(
                    chunks=chunks,
                    repository=repository_name,
                    file_path=relative_path,
                    language=language,
                    source_lines=source_lines,
                    symbol_type="method",
                    symbol_name=(
                        f"{class_name}.{method_name}"
                    ),
                    start_line=method_start,
                    end_line=method_end,
                    max_chunk_lines=max_chunk_lines,
                    overlap_lines=overlap_lines,
                    strategy="symbol",
                )

        # --------------------------------------------------
        # 2. Top-level functions
        # --------------------------------------------------

        for function_info in analysis.get(
            "functions",
            [],
        ):
            function_range = _get_valid_line_range(
                function_info,
                total_lines,
            )

            if function_range is None:
                continue

            function_start, function_end = function_range

            covered_ranges.append(
                function_range
            )

            function_name = function_info.get(
                "name",
                "unknown_function",
            )

            _add_chunks_for_range(
                chunks=chunks,
                repository=repository_name,
                language=language,
                file_path=relative_path,
                source_lines=source_lines,
                symbol_type="function",
                symbol_name=function_name,
                start_line=function_start,
                end_line=function_end,
                max_chunk_lines=max_chunk_lines,
                overlap_lines=overlap_lines,
                strategy="symbol",
            )

        # --------------------------------------------------
        # 3. Fallback chunks
        # --------------------------------------------------

        uncovered_ranges = _find_uncovered_ranges(
            total_lines,
            covered_ranges,
        )

        for fallback_start, fallback_end in uncovered_ranges:
            _add_chunks_for_range(
                chunks=chunks,
                repository=repository_name,
                file_path=relative_path,
                language=language,
                source_lines=source_lines,
                symbol_type="code_block",
                symbol_name=Path(relative_path).stem,
                start_line=fallback_start,
                end_line=fallback_end,
                max_chunk_lines=max_chunk_lines,
                overlap_lines=overlap_lines,
                strategy="line_fallback",
            )

    return chunks