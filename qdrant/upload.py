from argparse import ArgumentParser, Namespace

import numpy as np
import pandas as pd
import requests
from qdrant_client import QdrantClient, models
from tqdm.auto import tqdm


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--client-api-url", type=str, default="http://localhost:6333")
    parser.add_argument(
        "--collection-name",
        type=str,
        default="chefrag-ollama-bge-m3-567m-fp16",
    )
    parser.add_argument("--embedding-dim", type=int, default=1024)
    parser.add_argument("--chunks-file", type=str, default="data/chunks.parquet")
    parser.add_argument("--chunks-mmap", type=str, default="data/embeddings.mmap")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = QdrantClient(url=args.client_api_url)

    collection_exist_response = requests.get(
        url=f"{args.client_api_url}/collections/{args.collection_name}/exists"
    )
    collection_exist = collection_exist_response.json()["result"]["exists"]

    if not collection_exist:
        client.create_collection(
            collection_name=args.collection_name,
            vectors_config=models.VectorParams(
                size=args.embedding_dim, distance=models.Distance.COSINE
            ),
        )

    chunk_df = pd.read_parquet(args.chunks_file)
    chunk_mmap = np.memmap(
        filename=args.chunks_mmap,
        dtype=np.float32,
        shape=(chunk_df.shape[0], args.embedding_dim),
        mode="r",
    )

    client.upload_points(
        collection_name=args.collection_name,
        points=[
            models.PointStruct(
                id=idx,
                vector=chunk_mmap[idx].tolist(),
                payload={"text": row[1]["full_recipe"]},
            )
            for idx, row in enumerate(
                tqdm(chunk_df.iterrows(), total=chunk_df.shape[0])
            )
        ],
    )


if __name__ == "__main__":
    main()
