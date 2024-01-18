import pandas as pd
from time import time
from typing import Tuple, List
from shutil import rmtree
from os import mkdir
from os.path import isfile
import numpy as np

from extract import single_pdf_extract_process, CWD
from scrapers.arxiv import make_api_request, handle_xml, download_pdf

np.random.seed(2189)

CSV_PATH = "dataset/paper_data.csv"
SEP = "«"
MAX_RESULTS = 300
# up to 4 requests per second with 1s sleep
REQUEST_DELAY_S: float = 3
N_RETRIES: int = 3


def create_csv(path: str, columns=["url", "summary", "date"]) -> pd.DataFrame:
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, sep=SEP)
    return df


def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=SEP)


def add_to_csv(
    ids: List[str], summaries: List[str], dates: List[str], df: pd.DataFrame
) -> pd.DataFrame:
    new_df = pd.DataFrame(data={"url": ids, "summary": summaries, "date": dates})
    sum_df = pd.concat([df, new_df])
    return sum_df


def add_to_index_csv(
    file_paths: List[str],
    captions: List[str],
    summaries: List[str],
    df: pd.DataFrame,
) -> pd.DataFrame:
    new_df = pd.DataFrame(
        data={
            "file_path": file_paths,
            "captions": captions,
            "summary": summaries,
        }
    )
    sum_df = pd.concat([df, new_df])
    return sum_df


def save_df(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, sep=SEP)


def paper_info_loop() -> None:
    if not isfile(CSV_PATH):
        df = create_csv(CSV_PATH)
    else:
        df = load_csv(CSV_PATH)

    prev_time = time()
    n_papers = 0
    max_papers = 14000

    while n_papers < max_papers:
        new_time = time()
        if (new_time - prev_time) > REQUEST_DELAY_S:
            xml = make_api_request("all:microscopy", n_papers, MAX_RESULTS)
            ids, summaries, dates = handle_xml(xml)

            if len(ids) > 1:
                df = add_to_csv(ids, summaries, dates, df)
                save_df(df, CSV_PATH)
                n_papers += len(ids)
                print(f"Successful scrape of {len(ids)} papers. \nTotal N={n_papers}")
            prev_time = new_time


def strip_paper_name(name: str) -> str:
    return name.replace(".", "_")


def reset_tmp() -> None:
    try:
        rmtree("tmp")
    except FileNotFoundError:
        pass
    mkdir("tmp")
    mkdir("tmp/imgs")


def download_extract(url: str, summary: str, df: pd.DataFrame) -> pd.DataFrame:
    filename = strip_paper_name(url.split("/")[-1])
    download_pdf(url, f"tmp/{filename}.pdf")
    captions, img_paths = single_pdf_extract_process(
        f"{CWD}/tmp/{filename}.pdf", f"{CWD}/tmp/imgs/", f"{CWD}/tmp/", "dataset/imgs/"
    )
    summaries = [summary for i in range(len(captions))]
    new_df = add_to_index_csv(img_paths, captions, summaries, df)
    reset_tmp()
    return new_df


def download_pdf_loop(n_samples: int = 100) -> None:
    reset_tmp()
    names_df = load_csv("dataset/paper_data.csv")
    if not isfile("dataset/index.csv"):
        index_df = create_csv("dataset/index.csv", ["file_path", "captions", "summary"])
    else:
        index_df = load_csv("dataset/index.csv")
    reset_tmp()

    indices = np.arange(0, len(names_df.index))
    chosen_indices = np.random.choice(indices, size=n_samples, replace=False)

    i = 0
    stop = 100
    prev_time = time()
    while i < stop:
        new_time = time()
        if (new_time - prev_time) > REQUEST_DELAY_S:
            chosen_idx = chosen_indices[i]
            print(f"{new_time} [{i}/{stop}]: scraping paper {chosen_idx}")
            try:
                row = names_df.iloc[chosen_idx]
                url = row["url"]
                summary = row["summary"]
                index_df = download_extract(url, summary, index_df)
                save_df(index_df, "dataset/index.csv")
                i += 1
            except:
                print("Fail!")
                i += 1
            prev_time = new_time


if __name__ == "__main__":
    # print(CWD)
    # download_extract("http://arxiv.org/abs/2401.02538v1")
    download_pdf_loop()
    # paper_info_loop()
