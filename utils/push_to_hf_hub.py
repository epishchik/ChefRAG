import os
from argparse import ArgumentParser, Namespace

import pandas as pd
from datasets import Dataset, Features, Sequence, Value
from dotenv import load_dotenv

load_dotenv()


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "--recipes-filename", type=str, default="data/recipes_texts.csv"
    )
    parser.add_argument("--dataset-name", type=str, default="epishchik/RuRecipes-93k")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    recipes_df = pd.read_csv(args.recipes_filename)

    recipes_df["ingredients"] = recipes_df["ingredients"].apply(lambda x: eval(x))
    recipes_df["recipe"] = recipes_df["recipe"].apply(lambda x: eval(x))

    features = Features(
        {
            "link": Value("string"),
            "image_link": Value("string"),
            "title": Value("string"),
            "description": Value("string"),
            "ingredients": Sequence(Value("string")),
            "recipe": Sequence(Value("string")),
        }
    )

    hf_dataset = Dataset.from_pandas(df=recipes_df, features=features)
    hf_dataset.push_to_hub(repo_id=args.dataset_name, token=os.getenv("HF_TOKEN"))


if __name__ == "__main__":
    main()
