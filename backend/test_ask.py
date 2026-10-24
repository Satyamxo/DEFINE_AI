import argparse
import json

from app.rag.answer_generator import answer_question


def main():
    parser = argparse.ArgumentParser(
        description="Ask questions about a repository using DEFINE-AI."
    )

    parser.add_argument(
        "repository_path",
        help="Path to the repository.",
    )

    parser.add_argument(
        "question",
        help="Question about the repository.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of code chunks to retrieve.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("DEFINE-AI: REPOSITORY QUESTION ANSWERING")
    print("=" * 70)

    print(f"\nQuestion: {args.question}")
    print("\nRetrieving code and generating an answer...")

    result = answer_question(
        question=args.question,
        repository_root=args.repository_path,
        top_k=args.top_k,
    )

    print("\n" + "=" * 70)
    print("ANSWER")
    print("=" * 70)

    print(result["answer"])

    print("\n" + "=" * 70)
    print("RETRIEVED SOURCES")
    print("=" * 70)

    print(
        json.dumps(
            result["sources"],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()