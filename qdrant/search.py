from argparse import ArgumentParser, Namespace

import requests
from qdrant_client import QdrantClient


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--qdrant-api-url", type=str, default="http://localhost:6333")
    parser.add_argument(
        "--qdrant-collection-name",
        type=str,
        default="chefrag-ollama-bge-m3-567m-fp16",
    )
    parser.add_argument(
        "--ollama-api-url", type=str, default="http://localhost:11434/api/embed"
    )
    parser.add_argument("--ollama-model", type=str, default="bge-m3:567m-fp16")
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--topk", type=int, default=5)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    client = QdrantClient(url=args.qdrant_api_url)
    ollama_request_json = {
        "model": args.ollama_model,
        "input": args.query,
        "options": {"num_ctx": args.num_ctx},
    }

    ollama_response = requests.post(
        url=args.ollama_api_url, json=ollama_request_json, timeout=120
    )

    if ollama_response.status_code == 200:
        qdrant_response = client.query_points(
            collection_name=args.qdrant_collection_name,
            query=ollama_response.json()["embeddings"][0],
            with_payload=True,
            limit=args.topk,
        )

        recipes = []
        for point in qdrant_response.points:
            recipes.append(point.payload["recipe"])
        recipes = list(set(recipes))

        for recipe in recipes:
            print("-------------------------\n" + recipe, end="\n\n\n")
    else:
        print("Query encoding error.")


if __name__ == "__main__":
    main()
