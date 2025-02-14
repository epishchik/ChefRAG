import csv
import json
import random
import time
from argparse import ArgumentParser, Namespace
from parser.utils import sleep_random
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm


def get_page_content(url: str, agents: list[str]) -> str | None:
    headers = {"User-Agent": random.choice(agents)}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


def extract_recipe(html_content: str) -> tuple[list[str], str]:
    if not html_content:
        return [], []

    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except:  # noqa: E722
        return [], []

    try:
        ingredient_containers = soup.find("table", {"class": "ingr"})
        ingredient_spans = ingredient_containers.select("tr:not(:first-child) span")
        ingredients = [span.text.lower().strip() for span in ingredient_spans[2:]]
    except:  # noqa: E722
        ingredients = []

    try:
        recipe_containers = soup.find_all("div", {"class": "step_n"})
        steps = []
        for container in recipe_containers:
            steps.append(container.find("p").text.lower().strip())
    except:  # noqa: E722
        steps = []

    return ingredients, steps


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument(
        "--recipes-pages-filename", type=str, default="data/recipes_pages.csv"
    )
    parser.add_argument(
        "--recipes-texts-filename", type=str, default="data/recipes_texts.csv"
    )
    parser.add_argument("--agents", type=str, default="data/agents.json")
    parser.add_argument("--sleep", type=float, default=2.5)
    parser.add_argument("--sleep-std", type=float, default=0.8)

    return parser.parse_args()


def main():
    args = parse_args()

    read_filename = Path(args.recipes_pages_filename)
    write_filename = Path(args.recipes_texts_filename)

    with open(args.agents) as f:
        agents = json.load(f)

    read_csv_file = open(read_filename)
    write_csv_file = open(write_filename, "w+")

    csv_reader = csv.reader(read_csv_file)
    next(csv_reader, None)

    csv_writer = csv.writer(write_csv_file)
    csv_writer.writerow(["link", "ingredients", "recipe"])

    for _, url in tqdm(csv_reader):
        recipe_content = get_page_content(url=url, agents=agents)
        ingredients, recipe = extract_recipe(recipe_content)

        csv_writer.writerow([url, ingredients, recipe])

        sleep_duration = sleep_random(args.sleep, args.sleep_std)
        time.sleep(sleep_duration)

    read_csv_file.close()
    write_csv_file.close()


if __name__ == "__main__":
    main()
