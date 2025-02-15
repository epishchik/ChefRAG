from argparse import ArgumentParser, Namespace

import pandas as pd


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--filename", type=str, default="data/recipes_pages.csv")
    parser.add_argument(
        "--save-filename", type=str, default="data/recipes_pages_clean.csv"
    )
    parser.add_argument("--separator", type=str, default=",")
    parser.add_argument("--sort-column", type=str, default="title")
    parser.add_argument("--drop-column", type=str, default="link")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    recipes_pages = pd.read_csv(args.filename, sep=args.separator)
    recipes_pages = recipes_pages.drop_duplicates(subset=args.drop_column, keep="first")
    recipes_pages = recipes_pages.sort_values(by=args.sort_column)
    recipes_pages = recipes_pages.reset_index(drop=True)

    recipes_pages.to_csv(args.save_filename, sep=args.separator, index=False)


if __name__ == "__main__":
    main()
