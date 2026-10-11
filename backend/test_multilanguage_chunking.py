from pathlib import Path

from app.analyzer.repository_analyzer import analyze_repository
from app.rag.chunker import create_code_chunks


def test_multilanguage_chunks_preserve_language(tmp_path: Path):
    repository = tmp_path / "mixed_repo"
    repository.mkdir()

    (repository / "main.py").write_text(
        "def greet():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    (repository / "app.js").write_text(
        "export function runApp() {\n"
        "    return true;\n"
        "}\n",
        encoding="utf-8",
    )

    (repository / "utils.ts").write_text(
        "export function add(a: number, b: number): number {\n"
        "    return a + b;\n"
        "}\n",
        encoding="utf-8",
    )

    (repository / "App.tsx").write_text(
        "export function App() {\n"
        "    return <div>Hello</div>;\n"
        "}\n",
        encoding="utf-8",
    )

    analysis = analyze_repository(str(repository))

    chunks = create_code_chunks(
        repository_analysis=analysis,
        repository_root=str(repository),
    )

    assert chunks, "Expected the chunker to create code chunks."

    languages = {
        chunk["language"]
        for chunk in chunks
    }

    assert "python" in languages
    assert "javascript" in languages
    assert "typescript" in languages
    assert "tsx" in languages

    # Every chunk should preserve its language.
    for chunk in chunks:
        assert chunk["language"]
        assert chunk["file_path"]
        assert chunk["start_line"] >= 1
        assert chunk["end_line"] >= chunk["start_line"]
        assert chunk["code"].strip()