from pathlib import Path

from app.analyzer.dependency_analyzer import (
    build_dependency_graph_data,
)


def test_javascript_relative_import(tmp_path: Path):
    repository = tmp_path / "sample_repo"
    repository.mkdir()

    source_file = repository / "main.js"
    target_file = repository / "utils.js"

    source_file.write_text(
        'import { helper } from "./utils.js";\n',
        encoding="utf-8",
    )

    target_file.write_text(
        "export function helper() { return true; }\n",
        encoding="utf-8",
    )

    repository_analysis = {
        "repository": repository.name,
        "files": [
            {
                "path": "main.js",
                "analysis": {
                    "imports": [
                        {
                            "type": "module_import",
                            "module": "./utils.js",
                        }
                    ]
                },
            },
            {
                "path": "utils.js",
                "analysis": {
                    "imports": [],
                },
            },
        ],
    }

    result = build_dependency_graph_data(
        repository_analysis,
        str(repository),
    )

    assert {
        "source": "main.js",
        "target": "utils.js",
        "type": "IMPORTS",
    } in result["dependencies"]


def test_typescript_extension_resolution(tmp_path: Path):
    repository = tmp_path / "sample_repo"
    repository.mkdir()

    source_file = repository / "main.ts"
    target_file = repository / "helper.ts"

    source_file.write_text(
        'import { helper } from "./helper";\n',
        encoding="utf-8",
    )

    target_file.write_text(
        "export function helper(): boolean { return true; }\n",
        encoding="utf-8",
    )

    repository_analysis = {
        "repository": repository.name,
        "files": [
            {
                "path": "main.ts",
                "analysis": {
                    "imports": [
                        {
                            "type": "module_import",
                            "module": "./helper",
                        }
                    ]
                },
            },
        ],
    }

    result = build_dependency_graph_data(
        repository_analysis,
        str(repository),
    )

    assert {
        "source": "main.ts",
        "target": "helper.ts",
        "type": "IMPORTS",
    } in result["dependencies"]


def test_python_dependency_still_works(tmp_path: Path):
    repository = tmp_path / "sample_repo"
    repository.mkdir()

    source_file = repository / "main.py"
    target_file = repository / "helper.py"

    source_file.write_text(
        "from helper import run\n",
        encoding="utf-8",
    )

    target_file.write_text(
        "def run():\n    return True\n",
        encoding="utf-8",
    )

    repository_analysis = {
        "repository": repository.name,
        "files": [
            {
                "path": "main.py",
                "analysis": {
                    "imports": [
                        {
                            "type": "from_import",
                            "module": "helper",
                            "name": "run",
                        }
                    ]
                },
            },
        ],
    }

    result = build_dependency_graph_data(
        repository_analysis,
        str(repository),
    )

    assert {
        "source": "main.py",
        "target": "helper.py",
        "type": "IMPORTS",
    } in result["dependencies"]