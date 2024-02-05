from os import listdir
from json import load
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


def get_precision_recall(
    path: str,
    which_labels: str = "gpt3_5_with_abstract",
    which_eval: str = "gpt3_5_with_abstract_eval",
    eval_all: bool = False,
) -> None:
    total_n_fig = 0
    total_n_papers = 0
    tp_graph, tn_graph, fp_graph, fn_graph = 0, 0, 0, 0
    correct_instrument = 0
    correct_mat = 0
    for paper in listdir(path):
        try:
            with open(f"{path}{paper}/labels.json") as f:
                try:
                    data = load(f)
                except:
                    continue
        except FileNotFoundError:
            continue

        try:
            labels = data[which_labels]
            evals = data[which_eval]
        except KeyError:
            continue

        if len(labels) != len(evals):
            continue

        print(labels, evals)

        for i in range(len(evals)):
            print(i)
            label = labels[i]
            evaluation = evals[i]

            if (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == True
            ):
                tp_graph += 1
            elif (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == True
            ):
                tn_graph += 1
            elif (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == False
            ):
                fp_graph += 1
            elif (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == False
            ):
                fn_graph += 1

            if eval_all:
                if evaluation["instrument_correct"]:
                    correct_instrument += 1

                if evaluation["material_correct"]:
                    correct_mat += 1

            total_n_fig += 1
        total_n_papers += 1
    print(tp_graph, tn_graph, fp_graph, fn_graph)
    # print(correct_instrument - tn_graph)
    # print(correct_mat - tn_graph)

    print(total_n_fig, total_n_papers)


# TODO: add check micrograph code based on caption
# TODO: add check instrument code based on caption

if __name__ == "__main__":
    # get_precision_recall(
    #    "dataset/train/", "gpt3_5_without_abstract", "gpt3_5_without_abstract_eval_auto"
    # )
    get_precision_recall(
        "dataset/train/", "gpt3_5_with_abstract", "gpt3_5_with_abstract_eval"
    )
    # train_test_split("dataset", n_train=1500, filter_term="arxiv")


# w/out abstract: 291 1796 27 93
