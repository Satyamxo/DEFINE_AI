def build_context(
    chunks: list[dict],
    max_chars: int = 12000,
) -> str:
    """
    Format retrieved code chunks into a context string.

    Each chunk includes its source file and line range.
    The total context is bounded to control model usage.
    """

    if not chunks:
        return "No relevant code chunks were retrieved."

    sections = []
    current_length = 0

    for index, chunk in enumerate(chunks, start=1):
        file_path = chunk.get(
            "file_path",
            "Unknown file",
        )

        start_line = chunk.get(
            "start_line",
            "?",
        )

        end_line = chunk.get(
            "end_line",
            "?",
        )

        symbol_name = chunk.get(
            "symbol_name",
            "Unknown symbol",
        )

        symbol_type = chunk.get(
            "symbol_type",
            "Unknown type",
        )

        code = chunk.get("code", "")

        language = chunk.get("language", "text")

        section = (
            f"[Source {index}]\n"
            f"File: {file_path}\n"
            f"Language: {language}\n"
            f"Symbol: {symbol_name}\n"
            f"Type: {symbol_type}\n"
            f"Lines: {start_line}-{end_line}\n"
            f"Code:\n"
            f"```{language}\n{code}\n```\n"
        )

        

        remaining_chars = max_chars - current_length

        if remaining_chars <= 0:
            break

        if len(section) > remaining_chars:
            if not sections:
                # Keep at least part of the first chunk
                # if that chunk exceeds the entire limit.
                section = section[:max_chars]
                sections.append(section)

            break

        sections.append(section)
        current_length += len(section)

    return "\n".join(sections)