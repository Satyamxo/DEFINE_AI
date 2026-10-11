from pathlib import Path
from tempfile import TemporaryDirectory

from app.parser.tree_sitter_parser import (
    detect_language,
    parse_tree_sitter_file,
)


def test_language_detection():
    assert detect_language("App.js") == "javascript"
    assert detect_language("App.jsx") == "javascript"
    assert detect_language("App.ts") == "typescript"
    assert detect_language("App.tsx") == "tsx"
    assert detect_language("main.py") is None


def test_javascript_parser():
    source = """
import { helper } from "./utils";

class VideoProcessor {
    process(input) {
        return helper(input);
    }
}

function processVideo(url) {
    return new VideoProcessor().process(url);
}

const normalizeUrl = (url) => {
    return url.trim();
};
"""

    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "example.js"
        file_path.write_text(source, encoding="utf-8")

        result = parse_tree_sitter_file(file_path)

    assert result["language"] == "javascript"

    assert len(result["imports"]) == 1

    assert any(
        cls["name"] == "VideoProcessor"
        for cls in result["classes"]
    )

    video_processor = next(
        cls
        for cls in result["classes"]
        if cls["name"] == "VideoProcessor"
    )

    assert any(
        method["name"] == "process"
        for method in video_processor["methods"]
    )

    function_names = {
        function["name"]
        for function in result["functions"]
    }

    assert "processVideo" in function_names
    assert "normalizeUrl" in function_names

    assert result["has_syntax_errors"] is False


def test_typescript_parser():
    source = """
interface VideoInput {
    url: string;
}

export function processVideo(input: VideoInput): string {
    return input.url.trim();
}
"""

    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "example.ts"
        file_path.write_text(source, encoding="utf-8")

        result = parse_tree_sitter_file(file_path)

    assert result["language"] == "typescript"

    function_names = {
        function["name"]
        for function in result["functions"]
    }

    assert "processVideo" in function_names
    assert result["has_syntax_errors"] is False


def test_tsx_parser():
    source = """
import React from "react";

export function VideoCard() {
    return <div>Video</div>;
}
"""

    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "VideoCard.tsx"
        file_path.write_text(source, encoding="utf-8")

        result = parse_tree_sitter_file(file_path)

    assert result["language"] == "tsx"

    function_names = {
        function["name"]
        for function in result["functions"]
    }

    assert "VideoCard" in function_names
    assert result["has_syntax_errors"] is False