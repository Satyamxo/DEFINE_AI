DEFINE-AI — AI-Powered Repository Intelligence

Understand codebases. Explore software architecture. Ask questions about code using AI.

DEFINE-AI is an AI-powered repository intelligence system designed to help developers understand unfamiliar codebases. It analyzes repository structure, extracts code relationships, visualizes dependencies, and answers questions using Retrieval-Augmented Generation (RAG).

Instead of relying entirely on an LLM to understand a repository, DEFINE-AI combines static code analysis, graph-based visualization, hybrid retrieval, and a locally running language model to provide explanations grounded in source code.

1. Project Overview

Understanding an unfamiliar software repository can be time-consuming, especially when it contains multiple modules, classes, functions, and dependencies.

DEFINE-AI aims to simplify this process by combining repository analysis with AI-assisted code exploration.

Users can provide a GitHub repository URL, explore its structure through an interactive graph, inspect source files, and ask natural-language questions about the implementation.

The system uses static analysis to extract structural information and a RAG pipeline to retrieve relevant source code before generating answers.

Project Goals
Simplify exploration of unfamiliar repositories.
Visualize relationships between software components.
Retrieve relevant source code for natural-language questions.
Generate code explanations grounded in repository evidence.
Provide source references that users can inspect.
Support local LLM inference to reduce dependence on paid AI APIs.
Current Scope

The current implementation focuses on Python source-code analysis and repository question answering.

Support for additional programming languages and more advanced graph-aware reasoning are potential future improvements.

2. Problem Statement

Understanding a large or unfamiliar codebase often requires developers to manually inspect files, follow imports, trace function calls, and understand how individual components interact.

This creates several challenges:

Codebase complexity: Relationships between modules and functions can be difficult to understand.
Time-consuming exploration: Developers may spend significant time locating relevant implementation details.
Disconnected information: Source files, dependency relationships, and explanations are often explored separately.
Unreliable AI explanations: An LLM without relevant source-code context may produce incorrect or unsupported explanations.
Limited traceability: Developers need to verify explanations against the actual implementation.

DEFINE-AI addresses these challenges by combining structural repository analysis, interactive visualization, hybrid code retrieval, and context-grounded LLM responses.

The objective is to help developers move from a repository overview to specific implementation details with less manual effort.

3. Key Features
Repository Analysis
Accepts GitHub repository URLs.
Clones repositories through the backend.
Scans repository files.
Extracts Python classes, functions, methods, and imports using AST parsing.
Analyzes repository structure and dependencies.
Interactive Architecture Visualization
Builds a graph representation using NetworkX.
Displays repository relationships through React Flow.
Uses graph layout algorithms to organize nodes.
Supports node selection and nested expansion and collapse.
Displays additional information about selected nodes.
Source Code Exploration
Retrieves source files through the backend API.
Displays code with line numbers.
Supports source-range highlighting.
Connects graph exploration with code inspection.
Retrieval-Augmented Generation
Splits source code into retrieval-friendly chunks.
Preserves file paths, symbol names, and line ranges.
Generates embeddings using Sentence Transformers.
Stores embeddings and chunk metadata in a local vector index.
Combines semantic and keyword retrieval.
Uses weighted reciprocal-rank fusion to combine rankings.
Supplies retrieved code to an LLM for question answering.
AI Code Assistant
Accepts natural-language questions about a repository.
Uses retrieved source code to construct the LLM context.
Generates explanations through a local Ollama model.
Returns retrieved source metadata with answers.
Supports source navigation from the chat interface.
Local Inference

The RAG pipeline is designed to work with local embeddings and a locally running Ollama model, avoiding the need for a paid LLM API in the current development setup.

4. Architecture

DEFINE-AI consists of a React frontend, a FastAPI backend, a repository-analysis pipeline, and a RAG-based question-answering system.

High-Level Architecture
                    User
                     |
                     v
             React Frontend
          +--------------------+
          | Repository Input   |
          | Interactive Graph  |
          | Code Viewer        |
          | AI Chat Interface  |
          +--------------------+
                     |
                     v
               FastAPI Backend
                     |
          +----------+----------+
          |                     |
          v                     v
 Repository Analysis       RAG Pipeline
          |                     |
          v                     v
    Repository Scanner      Code Chunking
          |                     |
          v                     v
     Python AST Parser      Embeddings
          |                     |
          v                     v
 Dependency Analysis       Local Vector Index
          |                     |
          v                     v
    NetworkX Graph         Hybrid Retrieval
          |                     |
          v                     v
     Graph JSON             Context Builder
          |                     |
          v                     v
     React Flow             Local LLM
                                |
                                v
                         Generated Answer
                                |
                                v
                         Retrieved Sources
Repository Analysis Pipeline
A user submits a GitHub repository URL.
The backend clones the repository.
The scanner identifies supported source files.
The Python AST parser extracts structural information.
The analyzer and dependency-analysis components process the extracted information.
The graph builder constructs a graph representation.
The graph is serialized and returned to the frontend.
React Flow renders the graph for interactive exploration.
Question-Answering Pipeline
The user submits a question about the selected repository.
The retriever loads the repository's existing vector index.
The question is processed for semantic and keyword retrieval.
The retrieval system ranks relevant code chunks.
The context builder prepares source code and metadata for the LLM.
The local LLM generates an answer using the supplied context.
The backend returns the answer and retrieved source metadata.
The frontend displays the response and provides source-navigation controls.

The graph-analysis and RAG pipelines are currently separate components. Combining graph relationships with code retrieval for more advanced reasoning is a potential future improvement.

5. Technology Stack
Component	Technology	Purpose
Frontend	React	User interface
Styling	Tailwind CSS	Interface styling
Build tooling	Vite	Frontend development and bundling
Graph visualization	React Flow (@xyflow/react)	Interactive repository graph
Graph layout	Dagre	Graph node positioning
Backend	Python	Core application logic
API framework	FastAPI	HTTP API and frontend integration
Request validation	Pydantic	API request validation
Code parsing	Python AST	Extracting Python code structure
Graph construction	NetworkX	Representing repository relationships
Embeddings	Sentence Transformers	Generating vector representations
Embedding model	sentence-transformers/all-MiniLM-L6-v2	Semantic representations of code chunks
Numerical processing	NumPy	Storing and processing embedding arrays
Vector storage	Local NumPy index and JSON metadata	Persisting embeddings and source chunks
LLM runtime	Ollama	Local language-model inference
LLM	qwen2.5-coder:3b	Code-oriented answer generation
Version control	Git and GitHub	Source control

This table describes the current development stack. The exact versions should be documented using the project's actual dependency files.

6. How It Works

DEFINE-AI has two primary workflows: repository analysis and AI-powered question answering.

Workflow A: Repository Analysis

Step 1 — Repository Input

The user submits a GitHub repository URL through the React interface.

Step 2 — Repository Cloning

FastAPI receives the request and calls the repository manager to clone the repository.

Step 3 — Source Scanning

The scanner identifies files for analysis.

Step 4 — Structural Extraction

The Python AST parser extracts information such as imports, functions, classes, methods, and source-line ranges.

Step 5 — Dependency Analysis

The analyzer processes structural information to derive repository relationships.

Step 6 — Graph Construction

NetworkX represents the extracted components and relationships as a graph.

Step 7 — Visualization

The backend returns graph data, which the frontend renders using React Flow.

Users can select nodes, inspect details, expand graph sections, and open source files.

Workflow B: RAG-Based Question Answering

Step 1 — Code Chunking

Source code is divided into chunks using symbol information and line ranges.

The current chunker also handles uncovered code regions and splits larger ranges into smaller chunks.

Step 2 — Embedding Generation

The embedding model converts code chunks into numerical vector representations.

Step 3 — Index Persistence

The application stores the embeddings, chunk metadata, and index manifest locally.

Step 4 — Query Processing

When the user asks a question, the system performs semantic and keyword retrieval.

Step 5 — Hybrid Ranking

The retriever combines rankings using weighted reciprocal-rank fusion and additional identifier matching.

Step 6 — Context Construction

Relevant chunks are assembled into a context containing file paths, symbol names, line ranges, and source code.

Step 7 — Answer Generation

The context and question are sent to the local LLM through Ollama.

Step 8 — Answer and Sources

The backend returns the generated answer and metadata for the retrieved chunks.

The frontend displays the response and allows users to open source files associated with retrieved results.

The quality of the answer depends on retrieval quality, the available context, and the language model's ability to interpret that context correctly.

7. Installation
Prerequisites

Install the following software before setting up the project:

Git
Python 3.12
Conda or another Python environment manager
Node.js and npm
Ollama
A compatible local language model

The current setup uses a local embedding model and a local LLM. Initial model downloads require an internet connection.

Clone the Project

Clone the DEFINE-AI repository:

git clone <YOUR_DEFINE_AI_GITHUB_URL>
cd define-ai

Replace the placeholder with the actual URL of your DEFINE-AI repository.

Backend Installation

Navigate to the backend:

cd backend

Create a Conda environment:

conda create -n define-ai python=3.12

Activate it:

conda activate define-ai

Install Python dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt

If you already have an environment containing the project's dependencies, you can reuse it instead of creating another one.

Frontend Installation

Open a separate terminal and navigate to the frontend:

cd frontend

Install the dependencies:

npm install

The frontend uses the dependencies declared in its package manifest.

8. Environment Setup
Python Environment

The backend should run inside the Python environment containing the dependencies listed in backend/requirements.txt.

Activate the environment before starting the backend:

conda activate define-ai
Ollama Setup

Install Ollama using its official installation instructions.

Official website:

https://ollama.com/

Download the model used by the current configuration:

ollama pull qwen2.5-coder:3b

Confirm that the model is available:

ollama list

If the model name differs from the application's configuration, set the OLLAMA_MODEL environment variable to the installed model name.

For example, in PowerShell:

$env:OLLAMA_MODEL = "qwen2.5-coder:3b"

Ollama must be running and the model must be available before submitting questions to the AI assistant.

Embedding Model

The embedding implementation uses:

sentence-transformers/all-MiniLM-L6-v2

The model is loaded through Sentence Transformers and can be downloaded automatically when first required.

An authenticated Hugging Face account is not required for the current public embedding-model configuration.

Repository Storage

The backend stores cloned repositories in its configured repository directory.

The current development layout uses:

backend/
└── repositories/
RAG Index Storage

The local vector indexes are stored under:

backend/
└── data/
    └── rag_indexes/

Indexes are associated with repository paths. If a repository's source code changes, its index may need to be rebuilt.

Generated indexes and source-code chunks should not be committed to Git unless there is a specific, reviewed reason to include them.

9. Running the Backend

Open a terminal in the backend directory:

cd backend

Activate the environment:

conda activate define-ai

Start the FastAPI application:

uvicorn app.main:app --reload

The development API should be available at:

http://127.0.0.1:8000

Open the interactive API documentation:

http://127.0.0.1:8000/docs

The documentation can be used to inspect and test the available endpoints.

Main API Endpoints
Endpoint	Method	Purpose
/	GET	Check that the API is running
/health	GET	Basic health check
/repositories/clone	POST	Clone a GitHub repository
/repositories/analyze	POST	Clone and analyze a repository and return its graph
/repositories/{repository_name}/scan	GET	Scan a repository
/repositories/{repository_name}/analyze	GET	Analyze an existing repository
/repositories/{repository_name}/dependencies	GET	Retrieve dependency-analysis results
/repositories/{repository_name}/graph	GET	Retrieve repository graph data
/repositories/{repository_name}/files/{file_path}	GET	Read a source file
/repositories/{repository_name}/ask	POST	Ask a question about an indexed repository

The exact available routes should be verified against the current FastAPI application.

10. Running the Frontend

Open another terminal:

cd frontend

Start the Vite development server:

npm run dev

Open the local URL printed by Vite, typically:

http://localhost:5173
Using the Application
Enter a GitHub repository URL.
Select Analyze Repository.
Explore the generated repository graph.
Select graph nodes to inspect their details.
Open files through the code viewer.
Open the AI chat.
Ask questions about the selected repository.
Inspect the returned source files.
Click a source to open the corresponding code.

The backend must be running while using the frontend.

The current development API configuration points to:

http://127.0.0.1:8000

For production deployment, the API base URL should be configurable rather than hardcoded.

11. Indexing a Repository

Question answering requires a vector index for the selected repository.

The current development indexing script is:

backend/index_repository.py
Index the Example Repository

From the backend directory, run:

python index_repository.py ".\repositories\AI_Video_Ajent"

The indexing workflow performs the following operations:

Analyzes the repository.
Extracts structural information.
Creates source-code chunks.
Generates embeddings.
Saves the vector index and associated metadata.

The index is stored under:

backend/data/rag_indexes/

The actual index directory is generated by the vector-store implementation.

When Should an Index Be Rebuilt?

Rebuild the index when:

Source code changes significantly.
The chunking implementation changes.
The embedding model changes.
The existing index is missing or invalid.
You need to refresh the index after updating the repository.

The indexing process should not run unnecessarily for every chat question.

The current application expects an existing index when answering questions. Repository cloning and repository indexing are separate operations.

12. Asking Questions

Once a repository has been indexed, the AI assistant can answer questions using retrieved code.

Example Questions

Understanding a function

Explain how process_input works and what it returns.

Understanding execution flow

How does the application process a video URL
and transcribe its audio?

Understanding RAG implementation

How does this application retrieve relevant transcript
chunks and use them to answer questions?

Understanding architecture

Which components are involved in constructing the
RAG chain?

Understanding dependencies

Which functions and modules participate in this workflow?

The last question may require improvements to graph-aware retrieval, depending on the repository and the information available in the current RAG context.

How Answers Are Generated

The system retrieves relevant chunks, constructs a context, and sends it to the configured LLM.

The answer-generation prompt instructs the model to:

Base repository-specific claims on supplied code.
Avoid inventing functions, files, and APIs.
Acknowledge insufficient evidence.
Explain reasoning clearly.
Cite source files and line ranges.
Avoid claiming to have executed code that it did not execute.

These instructions help encourage grounded answers, but they do not guarantee that every generated answer or citation is correct.

Users should be able to inspect the underlying source code to verify important claims.

13. Evaluation Results

Status: Formal evaluation pending.

The RAG pipeline has been exercised with example repository questions, but a formal, repeatable evaluation dataset and verified quantitative results have not yet been established.

No accuracy, Recall@K, MRR, latency, or benchmark figures are claimed here.

Planned Evaluation

The next evaluation phase will measure retrieval quality, answer quality, citation accuracy, and application reliability.

Retrieval Evaluation

Create a verified dataset of repository questions with expected relevant files or symbols.

Potential metrics:

Metric	Purpose	Result
Recall@5	Measures how many relevant items appear in the top five results	Pending
MRR	Measures the rank of the first relevant result	Pending
Source-file hit rate	Measures how often a relevant source file is retrieved	Pending
Answer Evaluation

Assess whether generated answers:

Correctly describe the implementation.
Use relevant source code.
Provide valid file and line references.
Avoid unsupported implementation claims.
Acknowledge insufficient evidence.
Reliability Evaluation

Test:

Invalid repository URLs.
Missing indexes.
Invalid questions.
Unavailable LLM services.
Repository switching.
Source-file navigation.
Larger repositories and files.

Once the evaluation has been run, replace the pending entries with measured results and document the dataset, methodology, and limitations.

14. Limitations

DEFINE-AI is an evolving project, and the current implementation has several limitations.

Retrieval Quality

Hybrid retrieval combines semantic and keyword ranking, but relevant code may still be missed or ranked incorrectly.

Retrieval quality depends on the embedding model, chunking strategy, query wording, and repository structure.

Answer Accuracy

LLM-generated explanations can contain incorrect interpretations even when relevant source code is retrieved.

Source citations must be verified against the underlying implementation.

Context Limitations

The LLM receives selected source chunks rather than the entire repository. Some questions may require information that is not included in the retrieved context.

Local Hardware

Embedding generation and local LLM inference require computational resources. Response time and supported model sizes depend on available hardware and configuration.

Repository Size

Large repositories may increase cloning, parsing, indexing, memory, and retrieval costs. Performance limits have not yet been formally benchmarked.

Index Freshness

A saved index can become outdated when the underlying repository changes. Index refresh and invalidation must be handled appropriately.

Graph-Aware Reasoning

The repository graph and RAG pipeline currently operate as separate components. Full graph-aware question answering is a potential future improvement.

Deployment

The current setup is designed primarily for local development. Production deployment, multi-user isolation, authentication, rate limiting, and operational monitoring require additional work.


Project Status

DEFINE-AI has an implemented foundation for repository analysis, interactive graph visualization, code retrieval, and local-LLM question answering.

The current development focus is on completing the integrated user experience, evaluating RAG quality, improving reliability, and documenting reproducible setup and testing procedures.

The objective is not simply to generate AI explanations, but to help developers understand a codebase through inspectable repository structure and source-code evidence.

License

Add a license before publicly distributing the project. Until a license is selected and included, users should not assume that the repository grants permission to reuse, modify, or redistribute the code.
