from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.rag.answer_generator import answer_question
from app.rag.indexer import build_repository_index

from fastapi.middleware.cors import CORSMiddleware
from app.analyzer.repository_analyzer import analyze_repository
from app.repository.manager import clone_repository
from app.repository.scanner import scan_repository
from app.repository.code_reader import read_repository_file

from app.analyzer.dependency_analyzer import (
    build_dependency_graph_data,
)
from app.graph.builder import (
    build_repository_graph,
    graph_to_json,
)

app = FastAPI(
    title="Repository Intelligence API",
    description="AI-powered GitHub repository analysis system",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GitHubRepositoryRequest(BaseModel):
    github_url: str


class AskRepositoryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


@app.get("/")
def root():
    return {"message": "Repository Intelligence API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/repositories/clone")
def clone_repo(request: GitHubRepositoryRequest):

    try:
        result = clone_repository(request.github_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




@app.post("/repositories/analyze")
def analyze_github_repository(request: GitHubRepositoryRequest):
    try:
        # --------------------------------------------------
        # 1. Clone or obtain the repository
        # --------------------------------------------------

        clone_result = clone_repository(request.github_url)

        repository_name = clone_result["repository_name"]
        repository_path = Path(clone_result["path"]).resolve()

        if not repository_path.is_dir():
            raise FileNotFoundError(
                f"Repository directory not found: {repository_path}"
            )

        print(f"Repository: {repository_name}")
        print(f"Repository path: {repository_path}")

        # --------------------------------------------------
        # 2. Analyze repository
        # --------------------------------------------------

        repository_analysis = analyze_repository(
            str(repository_path)
        )

        # --------------------------------------------------
        # 3. Build dependency graph data
        # --------------------------------------------------

        dependency_data = build_dependency_graph_data(
            repository_analysis,
            str(repository_path),
        )

        # --------------------------------------------------
        # 4. Build graph
        # --------------------------------------------------

        graph = build_repository_graph(
            repository_analysis,
            dependency_data,
        )

        graph_data = graph_to_json(graph)

        # --------------------------------------------------
        # 5. Build RAG index automatically
        # --------------------------------------------------

        try:
            rag_index_result = build_repository_index(
                repository_path=str(repository_path),
                repository_analysis=repository_analysis,
            )

            print(
                f"RAG indexing completed: "
                f"{rag_index_result['total_chunks']} chunks"
            )

        except Exception as indexing_error:
            # Keep graph analysis available even if indexing fails.
            print(f"RAG INDEXING FAILED: {indexing_error}")

            rag_index_result = {
                "status": "failed",
                "error": str(indexing_error),
            }

        # --------------------------------------------------
        # 6. Return graph and RAG indexing status
        # --------------------------------------------------

        return {
            "repository": repository_name,
            "graph": graph_data,
            "rag_index": rag_index_result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    
@app.get("/repositories/{repository_name}/scan")
def scan_repo(repository_name: str):

    from pathlib import Path

    repository_path = (
        Path(__file__).resolve().parents[1] / "repositories" / repository_name
    )

    try:
        result = scan_repository(str(repository_path))
        return result
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

    

@app.get("/repositories/{repository_name}/analyze")
def analyze_repo(repository_name: str):

    from pathlib import Path

    repository_path = (
        Path(__file__).resolve().parents[2] / "repositories" / repository_name
    )

    try:
        result = analyze_repository(str(repository_path))
        return result
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get(
    "/repositories/{repository_name}/dependencies"
)
def get_dependencies(repository_name: str):

    from pathlib import Path

    repository_path = (
        Path(__file__).resolve().parents[1]
        / "repositories"
        / repository_name
    )

    try:

        # First analyze repository
        repository_analysis = analyze_repository(
            str(repository_path)
        )

        # Then build dependencies
        result = build_dependency_graph_data(
            repository_analysis,
            str(repository_path),
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
    
@app.get(
    "/repositories/{repository_name}/graph"
)
def get_repository_graph(
    repository_name: str,
):

    from pathlib import Path

    repository_path = (
        Path(__file__).resolve().parents[1]
        / "repositories"
        / repository_name
    )

    try:

        # -----------------------------------------
        # Analyze repository
        # -----------------------------------------

        repository_analysis = analyze_repository(
            str(repository_path)
        )

        # -----------------------------------------
        # Build dependencies
        # -----------------------------------------

        dependency_data = (
            build_dependency_graph_data(
                repository_analysis,
                str(repository_path),
            )
        )

        # -----------------------------------------
        # Build graph
        # -----------------------------------------

        graph = build_repository_graph(
            repository_analysis,
            dependency_data,
        )

        # -----------------------------------------
        # Convert to JSON
        # -----------------------------------------

        return graph_to_json(graph)

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )



PROJECT_ROOT = Path(__file__).resolve().parents[1]


@app.get(
    "/repositories/{repository_name}/files/{file_path:path}"
)
def get_repository_file(
    repository_name: str,
    file_path: str,
):

    repository_root = (
        PROJECT_ROOT
        / "repositories"
        / repository_name
    )

    try:

        return read_repository_file(
            repository_root,
            file_path,
        )

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.post("/repositories/{repository_name}/ask")
def ask_repository_question(
    repository_name: str,
    request: AskRepositoryRequest,
):
    # 1. Resolve the repository directory.
    repositories_root = (
    Path(__file__).resolve().parents[1] / "repositories"
).resolve()

    # 2. Reject invalid repository names.
    # Repository names must refer to a single directory.
    if (
        not repository_name
        or repository_name in {".", ".."}
        or "/" in repository_name
        or "\\" in repository_name
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid repository name.",
        )

    # 3. Resolve and validate the repository path.
    repository_path = (
        repositories_root / repository_name
    ).resolve()

    if not repository_path.is_relative_to(repositories_root):
        raise HTTPException(
            status_code=400,
            detail="Invalid repository path.",
        )

    # 4. Confirm that the repository exists.
    if not repository_path.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Repository not found.",
        )

    # 5. Retrieve relevant code and generate an answer.
    try:
        result = answer_question(
            question=request.question,
            repository_root=str(repository_path),
            top_k=request.top_k,
        )

        return result

    except FileNotFoundError:
        raise HTTPException(
            status_code=409,
            detail=(
                "This repository has not been indexed for "
                "question answering yet. Build its RAG index first."
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )