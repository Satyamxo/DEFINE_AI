from app.rag.context_builder import build_context
from app.rag.llm_client import generate_response
from app.rag.retriever import retrieve_relevant_chunks


SYSTEM_PROMPT = """
You are DEFINE-AI, an AI assistant that explains software repositories.

You answer questions about source code using retrieved repository evidence.

Rules:

1. Base factual claims about the repository on the supplied code context.
2. Never invent functions, files, classes, APIs, or implementation details.
3. If the supplied context does not contain enough evidence, clearly
   state that the available code context is insufficient.
4. Explain the reasoning in clear, understandable language.
5. When appropriate, explain the execution flow step by step.
6. Cite source files using this format:
   [path/to/file.py:L10-L25]
7. Only cite file paths and line ranges provided in the context.
8. Distinguish what the code explicitly shows from reasonable inferences.
9. Do not claim to have executed code or inspected files that were
   not supplied in the context.
"""


def answer_question(
    question: str,
    repository_root: str,
    top_k: int = 5,
) -> dict:
    """
    Answer a repository question using hybrid retrieval and an LLM.

    Returns the generated answer and its retrieved source chunks.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    chunks = retrieve_relevant_chunks(
        query=question,
        repository_root=repository_root,
        top_k=top_k,
    )

    if not chunks:
        return {
            "question": question,
            "answer": (
                "I could not retrieve relevant code from "
                "the repository to answer this question."
            ),
            "sources": [],
        }

    context = build_context(chunks)

    user_prompt = f"""
Repository question:

{question}

Retrieved repository context:

{context}

Answer the question using the available evidence.

Cite relevant sources in the format:
[path/to/file.py:L10-L25]

If the evidence is insufficient, explain what is missing.
"""

    answer = generate_response(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    sources = [
        {
            "file_path": chunk["file_path"],
            "symbol_name": chunk["symbol_name"],
            "symbol_type": chunk["symbol_type"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "similarity_score": chunk.get(
                "similarity_score"
            ),
            "hybrid_score": chunk.get(
                "hybrid_score"
            ),
        }
        for chunk in chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
    }