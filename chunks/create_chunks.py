from argparse import ArgumentParser, Namespace

import pandas as pd
from tqdm.auto import tqdm


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--raw-filename", type=str, default="data/recipes_texts.csv")
    parser.add_argument("--chunks-filename", type=str, default="data/chunks.parquet")
    parser.add_argument("--separator", type=str, default=",")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_df = pd.read_csv(args.raw_filename, sep=args.separator)

    raw_df["ingredients"] = raw_df["ingredients"].apply(lambda x: eval(x))
    raw_df["recipe"] = raw_df["recipe"].apply(lambda x: eval(x))

    chunk_idx = 0
    chunk_dct = {"id": [], "chunk": [], "full_recipe": []}
    for _, r in enumerate(tqdm(raw_df.iterrows(), total=raw_df.shape[0])):
        row = r[1]

        name = row["title"]
        full_recipe = [f"название рецепта: {name}"]

        description = row["description"]
        if description is not None and description != "nan":
            full_recipe.append(f"\nописание рецепта: {description}")

        ingredients = row["ingredients"]
        if ingredients is not None and ingredients != "nan" and len(ingredients) > 0:
            full_recipe.append(
                "\nингредиенты:\n"
                + "\n".join([f"* {ingredient}" for ingredient in ingredients])
            )

        recipe = row["recipe"]
        if recipe is not None and recipe != "nan" and len(recipe) > 0:
            full_recipe.append(
                "\nпошаговый рецепт:\n"
                + "\n".join(
                    [
                        f"шаг {step_idx + 1}: {step}"
                        for step_idx, step in enumerate(recipe)
                    ]
                )
            )

        full_recipe = "\n".join(full_recipe)

        chunk_dct["id"].append(chunk_idx)
        chunk_dct["chunk"].append(full_recipe)
        chunk_dct["full_recipe"].append(full_recipe)

        chunk_idx += 1

    chunk_df = pd.DataFrame(chunk_dct)
    chunk_df.to_parquet(args.chunks_filename)


if __name__ == "__main__":
    main()
