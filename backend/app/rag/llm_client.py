import os

from ollama import chat


MODEL_NAME = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5-coder:3b",
)


def generate_response(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    Generate a response using the configured local LLM.

    The model is served by Ollama.
    """

    if not system_prompt.strip():
        raise ValueError("System prompt cannot be empty.")

    if not user_prompt.strip():
        raise ValueError("User prompt cannot be empty.")

    response = chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        options={
            "temperature": 0.2,
            "num_ctx": 8192,
        },
    )

    return response.message.content.strip()