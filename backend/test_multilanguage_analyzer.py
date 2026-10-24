from pathlib import Path

from app.analyzer.repository_analyzer import analyze_repository


def test_multilanguage_repository_analysis(tmp_path: Path):
    """Verify that the analyzer processes Python, JS, TS and TSX."""

    repository = tmp_path / "mixed_repo"
    repository.mkdir()

    # 1. Python
    (repository / "main.py").write_text(
        "def greet():\n"
        "    return 'Hello from Python'\n",
        encoding="utf-8",
    )

    # 2. JavaScript
    (repository / "app.js").write_text(
        'import { helper } from "./helper.js";\n'
        "function runApp() {\n"
        "    return helper();\n"
        "}\n",
        encoding="utf-8",
    )

    (repository / "helper.js").write_text(
        "export function helper() {\n"
        "    return 'Hello from JavaScript';\n"
        "}\n",
        encoding="utf-8",
    )

    # 3. TypeScript
    (repository / "utils.ts").write_text(
        "export function add(a: number, b: number): number {\n"
        "    return a + b;\n"
        "}\n",
        encoding="utf-8",
    )

    # 4. TSX
    (repository / "App.tsx").write_text(
        'import React from "react";\n'
        "export function App() {\n"
        "    return <div>Hello from TSX</div>;\n"
        "}\n",
        encoding="utf-8",
    )

    result = analyze_repository(str(repository))

    files_by_name = {
        Path(file_info["path"]).name: file_info
        for file_info in result["files"]
    }

    print("\n--- ANALYZER DIAGNOSTICS ---")
    print("Total analyzed files:", result["total_files"])

    for name, file_info in files_by_name.items():
        analysis = file_info.get("analysis", {})

        print(f"\nFile: {name}")
        print("Language:", analysis.get("language"))
        print(
            "Functions:",
            [
                item.get("name")
                for item in analysis.get("functions", [])
            ],
        )
        print(
            "Classes:",
            [
                item.get("name")
                for item in analysis.get("classes", [])
            ],
        )
        print("Imports:", analysis.get("imports"))

    # All five files must be discovered and analyzed.
    assert result["total_files"] == 5, (
        f"Expected 5 files, found {result['total_files']}. "
        f"Discovered: {list(files_by_name)}"
    )

    # Python
    assert any(
        item["name"] == "greet"
        for item in files_by_name["main.py"]["analysis"]["functions"]
    )

    # JavaScript
    assert any(
        item["name"] == "runApp"
        for item in files_by_name["app.js"]["analysis"]["functions"]
    )

    # TypeScript
    assert any(
        item["name"] == "add"
        for item in files_by_name["utils.ts"]["analysis"]["functions"]
    )

    # TSX
    assert any(
        item["name"] == "App"
        for item in files_by_name["App.tsx"]["analysis"]["functions"]
    )

    # JavaScript import
    assert any(
        item.get("module") == "./helper.js"
        for item in files_by_name["app.js"]["analysis"]["imports"]
    )