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


def get_page_content(fid: int, page: int, agents: list[str]) -> str | None:
    url = f"https://www.russianfood.com/recipes/bytype/?fid={fid}&page={page}#rcp_list"
    headers = {"User-Agent": random.choice(agents)}

    response = requests.get(
        url="https://proxy.scrapeops.io/v1/",
        params={
            "api_key": os.getenv("SCRAPEOPS_API_KEY"),
            "url": url,
        },
        headers=headers,
        timeout=120,
    )

    if response.status_code == 200:
        return response.text
    return None


def extract_recipes(html_content: str) -> list[list[str]] | None:
    if not html_content:
        return None

    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except:  # noqa: E722
        return None
    outputs = []

    try:
        recipe_containers = soup.find_all("div", {"class": "in_seen"})
        if len(recipe_containers) < 1:
            return None
        for container in recipe_containers:
            link = "https://www.russianfood.com" + container.find("a")["href"]
            title = container.find("h3").text.lower().strip()
            outputs.append([title, link])
    except:  # noqa: E722
        return None

    return outputs


def get_max_pages_per_fid(
    agents: list[str],
    fid: int,
    high: int = 10,
) -> int:
    for page in tqdm(range(1, high + 1)):
        response = get_page_content(fid=fid, page=page, agents=agents)
        outputs = extract_recipes(response)
        if outputs is None:
            return page
    return page


def get_max_fid(agents: list[str], high: int = 10) -> int:
    for fid in tqdm(range(1, high + 1)):
        response = get_page_content(fid=fid, page=1, agents=agents)
        outputs = extract_recipes(response)
        if outputs is None:
            return fid
    return fid


def parse_args() -> Namespace:
    parser = ArgumentParser()

    parser.add_argument("--filename", type=str, default="data/recipes_pages.csv")
    parser.add_argument("--agents", type=str, default="data/agents.json")
    parser.add_argument("--high-fid", type=int, default=25)
    parser.add_argument("--max-fid", type=int, default=25)
    parser.add_argument("--start-fid", type=int, default=2)
    parser.add_argument("--high-page", type=int, default=50)
    parser.add_argument("--max-page", type=int, default=50)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--save-fid", type=str, default=None)
    parser.add_argument("--fid-file", type=str, default=None)

    return parser.parse_args()


def main():
    args = parse_args()

    filename = Path(args.filename)
    file_exist = filename.is_file()
    filename.parent.mkdir(parents=True, exist_ok=True)

    if args.save_fid is not None:
        save_fid_filename = Path(args.save_fid)
        save_fid_file_exist = save_fid_filename.is_file()
        save_fid_filename.parent.mkdir(parents=True, exist_ok=True)

        if not save_fid_file_exist:
            save_fid_csv_file = open(save_fid_filename, "w")
            save_fid_csv_writer = csv.writer(save_fid_csv_file)
            save_fid_csv_writer.writerow(["fid"])
        else:
            save_fid_csv_file = open(save_fid_filename, "a")
            save_fid_csv_writer = csv.writer(save_fid_csv_file)

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
        get_max_fid(agents=agents, high=args.high_fid)
        if args.max_fid == -1
        else args.max_fid
    )

    if args.fid_file is None:
        pbar = tqdm(range(args.start_fid, max_fid))
    else:
        fid_csv_file = open(args.fid_file)
        fid_csv_reader = csv.reader(fid_csv_file)
        next(fid_csv_reader, None)

        fids = []
        for row in fid_csv_reader:
            fids.append(row[0])
        fids = sorted(list(set(fids)))

        pbar = tqdm(fids, total=len(fids))
        fid_csv_file.close()

    for fid in pbar:
        max_page = (
            get_max_pages_per_fid(agents=agents, fid=fid, high=args.high_page)
            if args.max_page == -1
            else args.max_page
        )
        for page in range(args.start_page, max_page):
            page_content = get_page_content(fid=fid, page=page, agents=agents)

            outputs = extract_recipes(page_content)
            if outputs is not None:
                csv_writer.writerows(outputs)
                if args.save_fid is not None:
                    save_fid_csv_writer.writerow([fid])

    csv_file.close()
    if args.save_fid is not None:
        save_fid_csv_file.close()


if __name__ == "__main__":
    main()
