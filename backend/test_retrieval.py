import argparse

from app.rag.retriever import retrieve_relevant_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Test DEFINE-AI hybrid code retrieval."
    )

    parser.add_argument(
        "repository_path",
        help="Path to the repository being searched.",
    )

    parser.add_argument(
        "question",
        help="Question to search for.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("DEFINE-AI: HYBRID CODE SEARCH")
    print("=" * 70)

    print(f"\nQuestion: {args.question}")
    print("\nSearching repository...")

    results = retrieve_relevant_chunks(
        query=args.question,
        repository_root=args.repository_path,
        top_k=args.top_k,
    )

    print(f"\nRetrieved {len(results)} chunks.")

    for position, result in enumerate(
        results,
        start=1,
    ):
        print("\n" + "-" * 70)
        print(f"RESULT {position}")
        print("-" * 70)

        print(f"File: {result['file_path']}")
        print(f"Symbol: {result['symbol_name']}")
        print(f"Type: {result['symbol_type']}")

        print(
            f"Lines: {result['start_line']}-"
            f"{result['end_line']}"
        )

        print(
            f"Hybrid score: "
            f"{result['hybrid_score']:.4f}"
        )

        print(
            f"Semantic score: "
            f"{result['similarity_score']:.4f}"
        )

        print(
            f"Keyword score: "
            f"{result['keyword_score']:.4f}"
        )

        print(
            f"Semantic rank: "
            f"{result['semantic_rank']}"
        )

        print(
            f"Keyword rank: "
            f"{result['keyword_rank']}"
        )

        print(
            f"Identifier bonus: "
            f"{result['identifier_bonus']:.4f}"
        )

        print("\nCode:\n")
        print(result["code"][:1500])


if __name__ == "__main__":
    main()