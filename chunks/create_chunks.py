import re
from argparse import ArgumentParser, Namespace
from pathlib import Path, PurePath

import pandas as pd
from tqdm.auto import tqdm

from utils.safe_eval import safe_eval


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "--raw-filename", type=str, default="data/recipes_texts_clean.csv"
    )
    parser.add_argument("--chunks-folder", type=str, default="data")
    parser.add_argument("--separator", type=str, default=",")

    return parser.parse_args()


def full_recipe_chunks(raw_df: pd.DataFrame, save_folder: PurePath) -> None:
    chunk_idx = 0
    chunk_dct = {"id": [], "chunk": [], "full_recipe": []}

    for _, r in enumerate(tqdm(raw_df.iterrows(), total=raw_df.shape[0])):
        row = r[1]

        name = row["title"]
        full_recipe = [f"название рецепта: {name}"]

        description = row["description"]
        if pd.notna(description) and description != "nan":
            full_recipe.append(f"\nописание рецепта: {description}")

        ingredients = row["ingredients"]
        if ingredients and len(ingredients) > 0:
            full_recipe.append(
                "\nингредиенты:\n"
                + "\n".join([f"* {ingredient}" for ingredient in ingredients])
            )

        recipe = row["recipe"]
        if recipe and len(recipe) > 0:
            full_recipe.append(
                "\nпошаговый рецепт:\n"
                + "\n".join(
                    [
                        f"шаг {step_idx + 1}: {step}"
                        for step_idx, step in enumerate(recipe)
                    ]
                )
            )

        full_recipe_text = "\n".join(full_recipe)

        chunk_dct["id"].append(chunk_idx)
        chunk_dct["chunk"].append(full_recipe_text)
        chunk_dct["full_recipe"].append(full_recipe_text)

        chunk_idx += 1

    chunk_df = pd.DataFrame(chunk_dct)
    chunk_df.to_parquet(save_folder / "full_recipe_chunks.parquet")


def all_kinds_chunks(raw_df: pd.DataFrame, save_folder: PurePath) -> None:
    chunk_idx = 0
    chunk_list = []

    for recipe_id, row in enumerate(tqdm(raw_df.iterrows(), total=raw_df.shape[0])):
        row = row[1]
        title = row["title"]
        description = row["description"]
        ingredients = row["ingredients"]
        recipe = row["recipe"]

        if pd.notna(ingredients):
            cleaned_ingredients = re.sub(r"[\[\]']", "", ingredients)
            cleaned_ingredients = re.sub(r",\s*", "\n", cleaned_ingredients)
            ingredients_list = [
                f"* {ing.strip()}"
                for ing in cleaned_ingredients.split("\n")
                if ing.strip()
            ]
        else:
            ingredients_list = []

        if pd.notna(recipe):
            cleaned_recipe = re.sub(r"[\[\]']", "", recipe)
            cleaned_recipe = re.sub(r",\s*", ", ", cleaned_recipe)
            recipe_steps = re.split(r"\.,\s*", cleaned_recipe)
            recipe_steps = [step.strip() for step in recipe_steps if step.strip()]
        else:
            recipe_steps = []

        full_recipe = []
        if pd.notna(title):
            full_recipe.append(f"название рецепта: {title}")
        if pd.notna(description):
            full_recipe.append(f"\nописание рецепта: {description}")
        if ingredients_list:
            full_recipe.append("\nингредиенты:\n" + "\n".join(ingredients_list))
        if recipe_steps:
            full_recipe.append(
                "\nпошаговый рецепт:\n"
                + "\n".join(
                    [f"шаг {i+1}: {step}" for i, step in enumerate(recipe_steps)]
                )
            )
        full_recipe_text = "\n".join(full_recipe)

        if pd.notna(title):
            chunk_list.append(
                {
                    "chunk_id": chunk_idx,
                    "recipe_id": recipe_id,
                    "chunk_type": "title",
                    "chunk_text": title,
                    "full_recipe": full_recipe_text,
                }
            )
            chunk_idx += 1

        if pd.notna(description):
            chunk_list.append(
                {
                    "chunk_id": chunk_idx,
                    "recipe_id": recipe_id,
                    "chunk_type": "description",
                    "chunk_text": description,
                    "full_recipe": full_recipe_text,
                }
            )
            chunk_idx += 1

        if ingredients_list:
            ingredients_text = "\n".join(ingredients_list)
            chunk_list.append(
                {
                    "chunk_id": chunk_idx,
                    "recipe_id": recipe_id,
                    "chunk_type": "ingredients",
                    "chunk_text": ingredients_text,
                    "full_recipe": full_recipe_text,
                }
            )
            chunk_idx += 1

        if recipe_steps:
            for step in recipe_steps:
                chunk_list.append(
                    {
                        "chunk_id": chunk_idx,
                        "recipe_id": recipe_id,
                        "chunk_type": "recipe_part",
                        "chunk_text": step,
                        "full_recipe": full_recipe_text,
                    }
                )
                chunk_idx += 1

    chunk_df = pd.DataFrame(chunk_list)
    chunk_df.to_parquet(save_folder / "all_kinds_chunks.parquet")


def recipe_and_ingredients_chunks(raw_df: pd.DataFrame, save_folder: PurePath) -> None:
    chunk_list = []
    chunk_idx = 0

    for recipe_id, row in enumerate(tqdm(raw_df.iterrows(), total=raw_df.shape[0])):
        row = row[1]
        title = row["title"]
        description = row["description"]
        ingredients = row["ingredients"]
        recipe = row["recipe"]

        if pd.notna(ingredients):
            cleaned_ingredients = re.sub(r"[\[\]']", "", ingredients)  # delete [], '
            cleaned_ingredients = re.sub(
                r",\s*", "\n", cleaned_ingredients
            )  # replace commas with newlines
            ingredients_list = [
                f"* {ing.strip()}"
                for ing in cleaned_ingredients.split("\n")
                if ing.strip()
            ]
            ingredients_text = "\n".join(ingredients_list)
        else:
            ingredients_text = ""

        if pd.notna(recipe):
            cleaned_recipe = re.sub(r"[\[\]']", "", recipe)  # delete [], '
            recipe_steps = re.split(r"\.,\s*", cleaned_recipe)  # split by ".,"
            recipe_steps = [step.strip() for step in recipe_steps if step.strip()]
            recipe_text = "\n".join(
                [f"шаг {i+1}: {step}" for i, step in enumerate(recipe_steps)]
            )
            recipe_chunk_text = (
                f"название рецепта: {title}\nпошаговый рецепт:\n{recipe_text}"
            )
        else:
            recipe_chunk_text = f"название рецепта: {title}" if pd.notna(title) else ""

        full_recipe = []
        if pd.notna(title):
            full_recipe.append(f"название рецепта: {title}")
        if pd.notna(description):
            full_recipe.append(f"\nописание рецепта: {description}")
        if ingredients_list:
            full_recipe.append("\nингредиенты:\n" + "\n".join(ingredients_list))
        if recipe_steps:
            full_recipe.append(
                "\nпошаговый рецепт:\n"
                + "\n".join(
                    [f"шаг {i+1}: {step}" for i, step in enumerate(recipe_steps)]
                )
            )
        full_recipe_text = "\n".join(full_recipe)

        if recipe_chunk_text:
            chunk_list.append(
                {
                    "chunk_id": chunk_idx,
                    "recipe_id": recipe_id,
                    "chunk_type": "recipe",
                    "chunk_text": recipe_chunk_text,
                    "full_recipe": full_recipe_text,
                }
            )
            chunk_idx += 1

        if ingredients_text:
            chunk_list.append(
                {
                    "chunk_id": chunk_idx,
                    "recipe_id": recipe_id,
                    "chunk_type": "ingredients",
                    "chunk_text": ingredients_text,
                    "full_recipe": full_recipe_text,
                }
            )
            chunk_idx += 1

    chunk_df = pd.DataFrame(chunk_list)
    chunk_df.to_parquet(save_folder / "recipe_and_ingredients_chunks.parquet")


def main() -> None:
    args = parse_args()
    raw_df = pd.read_csv(args.raw_filename, sep=args.separator)

    save_folder = Path(args.chunks_folder)
    save_folder.mkdir(parents=True, exist_ok=True)

    all_kinds_chunks(raw_df, save_folder)
    recipe_and_ingredients_chunks(raw_df, save_folder)

    raw_df["ingredients"] = raw_df["ingredients"].apply(safe_eval)
    raw_df["recipe"] = raw_df["recipe"].apply(safe_eval)

    full_recipe_chunks(raw_df, save_folder)


if __name__ == "__main__":
    main()
