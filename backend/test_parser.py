from pathlib import Path

from app.parser.python_parser import parse_python_file


BASE_DIR = Path(__file__).resolve().parent.parent

file_path = (
    BASE_DIR
    / "repositories"
    / "AI_Video_Ajent"
    / "main.py"
)

result = parse_python_file(str(file_path))

print(result)