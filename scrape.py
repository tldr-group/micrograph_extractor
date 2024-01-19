from time import time
from typing import Tuple, List
from shutil import rmtree
from json import load
from os import mkdir, listdir
from os.path import isfile
import numpy as np

from extract import single_pdf_extract_process, CWD
from scrapers.generic import GenericScraper, make_folder
from scrapers.arxiv import ArxivScraper
from scrapers.chemrxiv import ChemrxivScraper

np.random.seed(2189)

MAX_RESULTS = 300
# up to 4 requests per second with 1s sleep
REQUEST_DELAY_S: float = 3
N_RETRIES: int = 3


def paper_info_loop(scraper: GenericScraper, query: str) -> None:
    prev_time = time()
    n_papers = 0
    max_papers = 14000

    while n_papers < max_papers:
        new_time = time()
        if (new_time - prev_time) > REQUEST_DELAY_S:
            new_paper_n = scraper.scrape(query, n_papers, 100)
            n_papers += new_paper_n
            prev_time = new_time


def reset_tmp() -> None:
    try:
        rmtree("tmp")
    except FileNotFoundError:
        pass
    mkdir("tmp")
    mkdir("tmp/imgs")
    #


def download_extract(scraper: GenericScraper, paper_path: str) -> None:
    with open("dataset/papers/" + paper_path + "/paper_data.json", "r") as f:
        data = load(f)
    id = data["url"]
    scraper.download_pdf(id, f"{CWD}/tmp/captions.pdf")
    make_folder(f"{CWD}/dataset/papers/{paper_path}/imgs")
    captions, img_paths = single_pdf_extract_process(
        f"{CWD}/tmp/captions.pdf",
        f"{CWD}/tmp/imgs/",
        f"{CWD}/dataset/papers/{paper_path}/",
        f"dataset/papers/{paper_path}/imgs/",
    )
    reset_tmp()


def download_pdf_loop(n_samples: int = 100) -> None:
    reset_tmp()
    papers = listdir("dataset/papers")
    n_papers = len(papers)

    indices = np.arange(0, n_papers)
    chosen_indices = np.random.choice(indices, size=n_samples, replace=False)

    scraper = ChemrxivScraper()

    i = 0
    stop = n_samples

    prev_time = time()
    while i < stop:
        new_time = time()
        if (new_time - prev_time) > REQUEST_DELAY_S:
            chosen_idx = i  # chosen_indices[i]
            chosen_paper_path = papers[chosen_idx]
            print(f"{new_time} [{i}/{stop}]: scraping paper {chosen_idx}")
            try:
                print(chosen_paper_path)
                download_extract(scraper, chosen_paper_path)
                i += 1
            except Exception as err:
                print("Fail!")
                print(err)
                i += 1
            prev_time = new_time


if __name__ == "__main__":
    print(CWD)
    # download_extract("http://arxiv.org/abs/2401.02538v1")
    # download_pdf_loop()

    # scraper = ArxivScraper()
    # paper_info_loop(scraper, "all:microscopy")
