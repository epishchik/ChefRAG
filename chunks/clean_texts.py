import json
import re
from argparse import ArgumentParser, Namespace

import pandas as pd

from utils.safe_eval import safe_eval


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--raw-filename", type=str, default="data/recipes_texts.csv")
    parser.add_argument(
        "--clean-filename", type=str, default="data/recipes_texts_clean.csv"
    )
    parser.add_argument(
        "--stop-chars-filename", type=str, default="data/stop_chars.json"
    )
    parser.add_argument("--separator", type=str, default=",")

    return parser.parse_args()


def clean_text(text: str, chars_to_remove: list[str]) -> str:
    if pd.isna(text) or not isinstance(text, str):
        return text
    pattern = "[" + re.escape("".join(chars_to_remove)) + "]"
    return re.sub(pattern, "", text)


def clean_list(lst: list[str], chars_to_remove: list[str]) -> list[str]:
    return [clean_text(item, chars_to_remove) for item in lst]


def clean() -> None:
    args = parse_args()
    raw_df = pd.read_csv(args.raw_filename, sep=args.separator)

    raw_df["ingredients"] = raw_df["ingredients"].apply(safe_eval)
    raw_df["recipe"] = raw_df["recipe"].apply(safe_eval)

    with open(args.stop_chars_filename) as f:
        chars_to_remove = json.load(f)

    raw_df["title"] = raw_df["title"].apply(lambda x: clean_text(x, chars_to_remove))
    raw_df["description"] = raw_df["description"].apply(
        lambda x: clean_text(x, chars_to_remove)
    )
    raw_df["ingredients"] = raw_df["ingredients"].apply(
        lambda x: clean_list(x, chars_to_remove)
    )
    raw_df["recipe"] = raw_df["recipe"].apply(lambda x: clean_list(x, chars_to_remove))

    raw_df.to_csv(args.clean_filename, index=False)


if __name__ == "__main__":
    clean()
