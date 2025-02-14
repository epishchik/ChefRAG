import csv
import json
import random
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm


def sleep_random(around: float, std: float) -> float:
    sleep_duration = random.normalvariate(around, std)
    sleep_duration = max(1.5, sleep_duration)
    return sleep_duration


def get_page_content(fid: int, page: int, agents: list[str]) -> str | None:
    url = f"https://www.russianfood.com/recipes/bytype/?fid={fid}&page={page}#rcp_list"
    headers = {"User-Agent": random.choice(agents)}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


def extract_recipes(html_content: str) -> list[list[str]]:
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    outputs = []

    recipe_containers = soup.find_all("div", {"class": "in_seen"})
    for container in recipe_containers:
        link = "https://www.russianfood.com" + container.find("a")["href"]
        title = container.find("h3").text.lower().strip()
        outputs.append([title, link])

    return outputs


def get_max_pages_per_fid(
    agents: list[str],
    fid: int,
    high: int = 10,
    sleep: float = 2.0,
    sleep_std: float = 0.5,
) -> int:
    for page in tqdm(range(1, high + 1)):
        response = get_page_content(fid=fid, page=page, agents=agents)
        if response is None:
            return page
        sleep_duration = sleep_random(sleep, sleep_std)
        time.sleep(sleep_duration)
    return page


def get_max_fid(
    agents: list[str], high: int = 10, sleep: float = 2.0, sleep_std: float = 0.5
) -> int:
    for fid in tqdm(range(1, high + 1)):
        response = get_page_content(fid=fid, page=1, agents=agents)
        if response is None:
            return fid
        sleep_duration = sleep_random(sleep, sleep_std)
        time.sleep(sleep_duration)
    return fid


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--filename", type=str, default="data/recipes_pages.csv")
    parser.add_argument("--agents", type=str, default="data/agents.json")
    parser.add_argument("--sleep", type=float, default=2.5)
    parser.add_argument("--sleep-std", type=float, default=0.8)
    parser.add_argument("--high-fid", type=int, default=10)
    parser.add_argument("--max-fid", type=int, default=10)
    parser.add_argument("--start-fid", type=int, default=2)
    parser.add_argument("--high-page", type=int, default=10)
    parser.add_argument("--max-page", type=int, default=10)
    parser.add_argument("--start-page", type=int, default=1)

    return parser.parse_args()


def main():
    args = parse_args()

    filename = Path(args.filename)
    file_exist = filename.is_file()
    filename.parent.mkdir(parents=True, exist_ok=True)

    with open(args.agents) as f:
        agents = json.load(f)

    if not file_exist:
        csv_file = open(filename, "w")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["title", "link"])
    else:
        csv_file = open(filename, "a")
        csv_writer = csv.writer(csv_file)

    max_fid = (
        get_max_fid(
            agents=agents,
            high=args.high_fid,
            sleep=args.sleep,
            sleep_std=args.sleep_std,
        )
        if args.max_fid == -1
        else args.max_fid
    )

    for fid in tqdm(range(args.start_fid, max_fid)):
        max_page = (
            get_max_pages_per_fid(
                agents=agents, fid=fid, high=args.high_page, sleep=args.sleep
            )
            if args.max_page == -1
            else args.max_page
        )
        for page in range(args.start_page, max_page):
            page_content = get_page_content(fid=fid, page=page, agents=agents)

            outputs = extract_recipes(page_content)
            csv_writer.writerows(outputs)

            sleep_duration = sleep_random(args.sleep, args.sleep_std)
            time.sleep(sleep_duration)

    csv_file.close()


if __name__ == "__main__":
    main()
