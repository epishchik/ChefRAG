from argparse import ArgumentParser, Namespace
from copy import deepcopy

import numpy as np
import pandas as pd
import requests
from tqdm.auto import tqdm


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "--api-url", type=str, default="http://localhost:11434/api/embed"
    )
    parser.add_argument("--model", type=str, default="bge-m3:567m-fp16")
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--chunks-file", type=str, default="data/chunks.parquet")
    parser.add_argument("--vectorize-column", type=str, default="chunk")
    parser.add_argument("--mmap-file", type=str, default="data/embeddings.mmap")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--embedding-dim", type=str, default=1024)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    chunk_df = pd.read_parquet(args.chunks_file)
    chunks = chunk_df[args.vectorize_column].to_list()

    mmap = np.memmap(
        filename=args.mmap_file,
        dtype=np.float32,
        shape=(chunk_df.shape[0], args.embedding_dim),
        mode="w+",
    )
    print(f"{mmap.shape = }")

    request_json_pattern = {
        "model": args.model,
        "input": None,
        "options": {"num_ctx": args.num_ctx},
    }
    print(f"{request_json_pattern = }")

    for batch_start in tqdm(range(0, chunk_df.shape[0], args.batch_size)):
        batch_end = min(batch_start + args.batch_size, chunk_df.shape[0])

        request_json = deepcopy(request_json_pattern)
        request_json["input"] = chunks[batch_start:batch_end]

        response = requests.post(url=args.api_url, json=request_json, timeout=120)

        if response.status_code == 200:
            response_json = response.json()

            for emb_idx, emb in enumerate(response_json["embeddings"]):
                mmap[batch_start + emb_idx, :] = np.array(emb).astype(np.float32)

            mmap.flush()


if __name__ == "__main__":
    main()
