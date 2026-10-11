from pathlib import Path
from git import Repo

BASE_REPOSITORY_DIR = Path(__file__).resolve().parents[2] / "repositories"


def clone_repository(github_url: str) -> dict:

    BASE_REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)

    repo_name = github_url.rstrip("/").split("/")[-1]

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]



    repository_path = BASE_REPOSITORY_DIR / repo_name

    if repository_path.exists():
        return{
            "status": "Already exists",
            "repository_name": repo_name,
            "path": str(repository_path) 
        }

    Repo.clone_from(github_url, str(repository_path))
    return{
        "status": "Cloned successfully",
        "repository_name": repo_name,
        "path": str(repository_path)
    }