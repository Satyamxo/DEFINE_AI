DEFINE-AI — AI-Powered Repository Intelligence

Understand codebases. Explore software architecture. Ask questions grounded in source code.

DEFINE-AI helps developers understand unfamiliar Python repositories through static code analysis, interactive dependency visualization, and Retrieval-Augmented Generation (RAG).

Given a GitHub repository, the system analyzes its structure, builds a graph of code components, and lets users inspect source files and ask natural-language questions. The RAG pipeline retrieves relevant code before sending context to a locally running language model.

Current scope: Python-focused repository analysis and repository question answering.

Key Features

Repository analysis: Clone a GitHub repository and scan supported source files.

Python AST parsing: Extract classes, functions, methods, imports, and source locations.

Dependency graph: Represent repository components and relationships with NetworkX.

Interactive visualization: Explore graph nodes using React Flow, including node selection and nested expansion/collapse.

Source-code viewer: Open repository files and inspect source code with line numbers.

Hybrid retrieval: Combine semantic and keyword-based retrieval, with weighted Reciprocal Rank Fusion (RRF) to combine rankings.

Code-aware chunking: Preserve file paths, symbol names, and line-range metadata with source chunks.

RAG-based Q&A: Ask questions about an indexed repository and receive answers based on retrieved code context.

Local inference: Generate answers using an Ollama-hosted language model and local embeddings.

Screenshots

Add screenshots captured from the running application to docs/images/, then update the filenames below.

Repository Graph



Source Code Exploration



AI Repository Q&A



Architecture

DEFINE-AI has two main workflows: repository analysis and RAG-based question answering.

1. Repository Analysis

GitHub Repository URL
        |
        v
Repository Manager
        |
        v
Repository Scanner
        |
        v
Python AST Parser
        |
        v
Dependency Analysis
        |
        v
NetworkX Graph Builder
        |
        v
Graph JSON
        |
        v
React Flow Visualization

2. RAG-Based Question Answering

Repository Source Code
        |
        v
Code Chunking + Metadata
        |
        v
Sentence Transformers Embeddings
        |
        v
Local Vector Index
        |
User Question
        |
        v
Hybrid Retrieval
        |
        v
Rank Fusion + Identifier Matching
        |
        v
Context Construction
        |
        v
Local LLM through Ollama
        |
        v
Answer + Retrieved Source Metadata

The graph-analysis and RAG workflows are separate components in the current implementation. The diagram does not imply that graph relationships are automatically used during retrieval.

Technology Stack

Component

Technology

Purpose

Frontend

React

User interface

Styling

Tailwind CSS

Interface styling

Build tooling

Vite

Frontend development and bundling

Graph visualization

React Flow (@xyflow/react)

Interactive repository graph

Graph layout

Dagre

Graph node positioning

Backend

Python, FastAPI

Application logic and HTTP API

Request validation

Pydantic

API request validation

Code parsing

Python AST

Extract Python code structure

Graph construction

NetworkX

Represent repository relationships

Embeddings

Sentence Transformers

Generate vector representations of code chunks

Embedding model

sentence-transformers/all-MiniLM-L6-v2

Text/code-chunk embeddings

Numerical processing

NumPy

Process embedding arrays

Local LLM runtime

Ollama

Run the configured language model locally

LLM

qwen2.5-coder:3b

Code-oriented answer generation

Version control

Git and GitHub

Source control

The listed model names reflect the documented development configuration. Check the application configuration and dependency files if you have changed them.

How It Works

Repository Analysis

The user submits a GitHub repository URL.

The backend clones the repository.

The scanner identifies supported source files.

Python AST parsing extracts structural information such as imports, classes, functions, methods, and source-line ranges.

Dependency-analysis components process the extracted information.

NetworkX builds the repository graph.

The backend returns graph data for rendering in React Flow.

Users can select graph nodes, inspect component details, and open source files.

RAG-Based Question Answering

Source code is divided into chunks using symbol information and line ranges.

Sentence Transformers generates embeddings for the chunks.

The application stores the embeddings and associated metadata in a local index.

A user's question is processed using semantic and keyword retrieval.

Weighted Reciprocal Rank Fusion combines retrieval rankings; identifier matching can help surface code related to specific names.

The context builder assembles relevant chunks with file paths, symbol names, line ranges, and source code.

The context and question are sent to the configured local LLM through Ollama.

The backend returns the answer and retrieved-source metadata for inspection in the frontend.

Answer quality depends on retrieval quality, the available context, and the language model. Verify important claims against the source code.

Prerequisites

Install the following before running the project:

Git

Python 3.12 (or the version supported by the backend dependencies)

Node.js and npm

Conda or another Python environment manager

Ollama

Sufficient disk space for the repository, dependencies, embedding model, and LLM

The first model download requires an internet connection.

Installation

1. Clone the Repository

Replace the placeholder with the actual GitHub URL for DEFINE-AI.

git clone https://github.com/Satyamxo/Define-ai/
cd define ai

2. Set Up the Backend

From the project root:

cd backend
conda create -n define-ai python=3.12
conda activate define-ai
python -m pip install --upgrade pip
pip install -r requirements.txt

If you already have a compatible environment, activate it instead of creating another one.

3. Set Up the Frontend

Open a separate terminal from the project root:

cd frontend
npm install

4. Set Up Ollama

Install Ollama using its official instructions: ollama.com.

Download the model used by the documented configuration:

ollama pull qwen2.5-coder:3b
ollama list

Make sure Ollama is running and the model is available before asking questions. If your application configuration uses a different model, pull that model and update the relevant configuration accordingly.

5. Embedding Model

The documented embedding model is:

sentence-transformers/all-MiniLM-L6-v2

Sentence Transformers may download the model automatically the first time it is needed.

Run the Application

Start the Backend

From the backend directory, with the define-ai environment activated:

uvicorn app.main:app --reload

The API is expected to be available at http://127.0.0.1:8000 if that is the host and port configured by the application.

Interactive API documentation is typically available at:

http://127.0.0.1:8000/docs

Confirm the import path and routes against the current backend code if your project structure differs.

Start the Frontend

In a separate terminal:

cd frontend
npm run dev

Open the local URL printed by Vite, typically http://localhost:5173.

The backend must be running while using the frontend. The frontend's API base URL must point to the running backend.

Index a Repository for Q&A

The repository must be indexed before asking questions about its code.

The documented indexing script is backend/index_repository.py. From the backend directory, run:

python index_repository.py "./repositories/<REPOSITORY_FOLDER>"

Replace <REPOSITORY_FOLDER> with the actual directory name of the cloned repository. For example, if the repository folder is AI_Video_Agent:

python index_repository.py "./repositories/AI_Video_Agent"

The indexing workflow analyzes the repository, creates source-code chunks, generates embeddings, and saves the index and associated metadata under the configured RAG index directory (documented as backend/data/rag_indexes/).

Repository cloning and indexing are separate operations. Rebuild the index when the source code changes or when the chunking or embedding configuration changes.

Using DEFINE-AI

Start the backend and frontend.

Enter a GitHub repository URL in the application.

Analyze the repository.

Explore the generated graph and select nodes to inspect components.

Open source files in the code viewer.

Ensure the repository has been indexed for RAG.

Open the AI chat and ask a question about the repository.

Inspect the retrieved source metadata and verify important answers against the code.

Example Questions

Explain how process_input works and what it returns.

How does the application process a video URL and transcribe its audio?

How does this repository create embeddings and retrieve relevant code?

Which components are involved in constructing the RAG pipeline?

Which source files are relevant to this functionality?

The answer depends on the repository being indexed and the code retrieved for the question.

Repository and Index Storage

The documented development layout stores cloned repositories under:

backend/
└── repositories/

RAG indexes are documented as being stored under:

backend/
└── data/
    └── rag_indexes/

These paths depend on the current application configuration. Avoid committing cloned repositories, generated indexes, virtual environments, environment files, API keys, or other local artifacts unless there is a deliberate reason to include them.

Project Status

DEFINE-AI brings together Python repository analysis, interactive graph visualization, hybrid code retrieval, and local-LLM question answering in one developer-focused application.
