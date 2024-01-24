from os import listdir
from shutil import copytree, rmtree
import numpy as np


from scrapers.generic import make_folder

np.random.seed(2189)


def train_test_split(
    dataset_path: str, n_train: int = 500, n_test: int = 2500, filter_term: str = "none"
) -> None:
    papers = listdir(f"{dataset_path}/papers")
    n_papers = len(papers)

    indices = np.arange(0, n_papers)
    chosen_indices = np.random.choice(indices, size=n_train + n_test, replace=False)
    train_inds = chosen_indices[:n_train]
    test_inds = chosen_indices[n_train:]

    for folder in [f"{dataset_path}/train", f"{dataset_path}/test"]:
        try:
            rmtree("tmp")
        except FileNotFoundError:
            pass
            make_folder(folder)

    for i in train_inds:
        paper = papers[i]
        if filter_term in paper:
            continue

        try:
            copytree(f"{dataset_path}/papers/{paper}", f"{dataset_path}/train/{paper}")
        except FileExistsError:
            pass
    for i in test_inds:
        paper = papers[i]
        if filter_term in paper:
            continue

        try:
            copytree(f"{dataset_path}/papers/{paper}", f"{dataset_path}/test/{paper}")
        except FileExistsError:
            pass


def detect_composite_image_from_caption(caption: str) -> bool:
    if "(a)" in caption.lower() or " a. " in caption.lower():
        return True
    else:
        return False


# TODO: add check micrograph code based on caption
# TODO: add check instrument code based on caption

if __name__ == "__main__":
    train_test_split("dataset", n_train=1500, filter_term="arxiv")
