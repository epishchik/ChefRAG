import csv
import json
import os
import random
from argparse import ArgumentParser, Namespace
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm.auto import tqdm

load_dotenv()


def get_page_content(url: str, agents: list[str]) -> str | None:
    headers = {"User-Agent": random.choice(agents)}

    response = requests.get(
        url="https://proxy.scrapeops.io/v1/",
        params={
            "api_key": os.getenv("SCRAPEOPS_API_KEY"),
            "url": url,
        },
        headers=headers,
    )

    if response.status_code == 200:
        return response.text
    return None


def extract_recipe(html_content: str) -> tuple[str, str, str, list[str], list[str]]:
    if not html_content:
        return None, None, None, [], []

    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except:  # noqa: E722
        return None, None, None, [], []

    try:
        ingredient_containers = soup.find("table", {"class": "ingr"})
        ingredient_spans = ingredient_containers.select("tr:not(:first-child) span")
        ingredients = [span.text.lower().strip() for span in ingredient_spans]

        if ingredients[0] == "продукты":
            ingredients = ingredients[1:]

        if "на" in ingredients[0] and (
            "порций" in ingredients[0]
            or "порцию" in ingredients[0]
            or "порции" in ingredients[0]
        ):
            ingredients = ingredients[1:]
    except:  # noqa: E722
        ingredients = []

    try:
        recipe_containers = soup.find_all("div", {"class": "step_n"})
        if len(recipe_containers) < 1:
            raise
        steps = []
        for container in recipe_containers:
            steps.append(container.find("p").text.lower().strip())
    except:  # noqa: E722
        try:
            recipe_container = soup.find("div", {"id": "how"})
            recipe_text = recipe_container.get_text(separator="\n", strip=True)
            steps = [t.lower().strip() for t in recipe_text.split("\n")]
        except:  # noqa: E722
            steps = []

    try:
        metadata = soup.find("div", {"class": "ya-share2 share_block"})
    except:  # noqa: E722
        return None, None, None, ingredients, steps

    try:
        image_url = metadata["data-image"]
    except:  # noqa: E722
        image_url = None

    try:
        title = metadata["data-title"].lower().strip()
    except:  # noqa: E722
        title = None

    try:
        description = metadata["data-description"].lower().strip()
    except:  # noqa: E722
        description = None

    return image_url, title, description, ingredients, steps


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "--recipes-pages-filename", type=str, default="data/recipes_pages.csv"
    )
    parser.add_argument(
        "--recipes-texts-filename", type=str, default="data/recipes_texts.csv"
    )
    parser.add_argument("--agents", type=str, default="data/agents.json")
    parser.add_argument("--total", type=int, default=-1)
    parser.add_argument("--skip-first-n", type=int, default=-1)

    return parser.parse_args()


def main():
    args = parse_args()

    read_filename = Path(args.recipes_pages_filename)
    write_filename = Path(args.recipes_texts_filename)

    write_file_exist = write_filename.is_file()
    write_filename.parent.mkdir(parents=True, exist_ok=True)

    with open(args.agents) as f:
        agents = json.load(f)

    read_csv_file = open(read_filename)

    if not write_file_exist:
        write_csv_file = open(write_filename, "w")
        csv_writer = csv.writer(write_csv_file)
        csv_writer.writerow(
            ["link", "image_link", "title", "description", "ingredients", "recipe"]
        )
    else:
        write_csv_file = open(write_filename, "a")
        csv_writer = csv.writer(write_csv_file)

    csv_reader = csv.reader(read_csv_file)
    next(csv_reader, None)

    if args.skip_first_n != -1:
        for _ in tqdm(range(args.skip_first_n), desc="skipping"):
            next(csv_reader, None)

    total = 0
    for _, url in tqdm(csv_reader):
        recipe_content = get_page_content(url=url, agents=agents)

        image_url, title, description, ingredients, recipe = extract_recipe(
            recipe_content
        )

        csv_writer.writerow([url, image_url, title, description, ingredients, recipe])
        total += 1

        if args.total != -1 and total >= args.total:
            break

    read_csv_file.close()
    write_csv_file.close()


if __name__ == "__main__":
    main()
