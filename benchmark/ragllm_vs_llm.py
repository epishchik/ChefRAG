from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from tqdm.auto import tqdm
from vllm import LLM


def cosine_similarity(a: np.memmap, b: np.memmap) -> float:
    a_norm = a / np.linalg.norm(a, ord=2)
    b_norm = b / np.linalg.norm(b, ord=2)

    per_sample_sim = np.sum(a_norm * b_norm, axis=1)
    return per_sample_sim.mean()


class TextDataset(torch.utils.data.Dataset):
    def __init__(self, texts: list[str]) -> None:
        self.texts = texts

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> str:
        return self.texts[idx]


def collate_fn(batch: Iterable) -> list[str]:
    texts = []
    for item in batch:
        texts.append(item)
    return texts


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--process-raw-df", action="store_true")
    parser.add_argument(
        "--score-filename", type=str, default="data/ragllm_vs_llm.parquet"
    )
    parser.add_argument("--save-folder", type=str, default="data/bench")
    parser.add_argument("--gt-column", type=str, default="ground_truth_answer")
    parser.add_argument("--llm-column", type=str, default="llm_answer")
    parser.add_argument(
        "--rag-llm-column", type=str, default="rag_llm_full_recipe_answer"
    )
    parser.add_argument("--mmap-length", type=int)
    return parser.parse_args()


def _vectorize(
    llm_model: LLM,
    texts: list[str],
    mmap_filename: PurePath,
    batch_size: int = 256,
    workers: int = 16,
    flush_every: int = 100,
) -> np.memmap:
    dataset = TextDataset(texts=texts)
    dataloader = torch.utils.data.DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=workers,
        collate_fn=collate_fn,
    )

    mmap = np.memmap(
        filename=mmap_filename, shape=(len(dataset), 3584), dtype=np.float32, mode="w+"
    )

    with torch.no_grad(), torch.amp.autocast("cuda"):
        for batch_idx, batch in enumerate(tqdm(dataloader, total=len(dataloader))):
            embs = llm_model.encode(batch, use_tqdm=False)

            batch_start = batch_idx * batch_size
            for emb_idx, emb in enumerate(embs):
                mmap[batch_start + emb_idx, :] = np.array(
                    emb.outputs.embedding, dtype=np.float32
                )

            if (batch_idx + 1) % flush_every == 0:
                mmap.flush()

        mmap.flush()


def vectorize_df(
    df: pd.DataFrame,
    gt_column: str,
    llm_column: str,
    rag_llm_column: str,
    save_folder: PurePath,
) -> None:
    llm = LLM(model="BAAI/bge-multilingual-gemma2")

    _vectorize(
        llm_model=llm,
        texts=df[gt_column].to_list(),
        mmap_filename=save_folder / "gt.mmap",
    )

    _vectorize(
        llm_model=llm,
        texts=df[llm_column].to_list(),
        mmap_filename=save_folder / "llm.mmap",
    )

    _vectorize(
        llm_model=llm,
        texts=df[rag_llm_column].to_list(),
        mmap_filename=save_folder / "rag_llm.mmap",
    )


def main() -> None:
    args = parse_args()

    save_folder = Path(args.save_folder)
    save_folder.mkdir(parents=True, exist_ok=True)

    if args.process_raw_df:
        score_df = pd.read_parquet(args.score_filename)
        vectorize_df(
            score_df,
            args.gt_column,
            args.llm_column,
            args.rag_llm_column,
            save_folder,
        )

    shape = score_df.shape[0] if args.process_raw_df else args.mmap_length

    gt_mmap = np.memmap(
        filename=save_folder / "gt.mmap",
        shape=(shape, 3584),
        dtype=np.float32,
        mode="r",
    )

    llm_mmap = np.memmap(
        filename=save_folder / "llm.mmap",
        shape=(shape, 3584),
        dtype=np.float32,
        mode="r",
    )

    rag_llm_mmap = np.memmap(
        filename=save_folder / "rag_llm.mmap",
        shape=(shape, 3584),
        dtype=np.float32,
        mode="r",
    )

    cos1 = cosine_similarity(gt_mmap, llm_mmap)
    cos2 = cosine_similarity(gt_mmap, rag_llm_mmap)

    print(f"Similarity for LLM answers = {cos1:.4f}")
    print(f"Similarity for RAG-LLM answers = {cos2:.4f}")


if __name__ == "__main__":
    main()
