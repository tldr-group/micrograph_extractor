import os
from os import listdir
from json import load
from shutil import copytree, rmtree
import numpy as np
from typing import List, Tuple


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


def evaluate_labels(train_folder, label_type):
    for doi_folder in os.listdir(train_folder):
        doi_path = os.path.join(train_folder, doi_folder)
        if os.path.isdir(doi_path):
            label_file = os.path.join(doi_path, "labels.json")
            if os.path.isfile(label_file):
                with open(label_file, "r", encoding="utf-8") as file:
                    labels = json.load(file)

                # Check if 'human' field exists, if not, skip
                if "human" not in labels:
                    print(f"Skipping {doi_folder}, 'human' field not found.")
                    continue

                llm_eval = []

                human_labels = labels.get("human", [])
                llm_labels = labels.get(label_type, [])

                llm_dict = {item["figure"]: item for item in llm_labels}

                for human_item in human_labels:
                    figure = human_item["figure"]
                    # compare with llm
                    llm_item = llm_dict.get(figure)
                    if llm_item:
                        isMicrograph_correct = (
                            llm_item["isMicrograph"] == human_item["isMicrograph"]
                        )
                    else:
                        print(f"No {label_type} item for figure: {figure}")
                        isMicrograph_correct = False
                    llm_eval.append(
                        {"figure": figure, "isMicrograph_correct": isMicrograph_correct}
                    )

                # update evaluated labels and save
                labels[f"{label_type}_eval_auto"] = llm_eval
                with open(label_file, "w", encoding="utf-8") as file:
                    json.dump(labels, file, ensure_ascii=False, indent=4)


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
) -> Tuple[List[int], List[int], List[str], List[int]]:
    total_n_fig = 0
    total_n_papers = 0
    tp_graph, tn_graph, fp_graph, fn_graph = 0, 0, 0, 0
    correct_instrument = 0
    correct_mat = 0

    is_micrograph: List[int] = []
    is_correct: List[int] = []
    papers: List[str] = []
    fig_nums: List[int] = []

    def _handle_error() -> None:
        is_micrograph.append(-1)
        is_correct.append(-1)

    def get_eval(evals: List[dict], fig_n: int) -> dict:
        for d in evals:
            if int(d["figure"]) == fig_n:
                return d
            else:
                pass

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

        for i in range(len(labels)):
            # print(i)
            label = labels[i]
            fig_num = int(label["figure"])
            # print(fig_num)
            evaluation = get_eval(evals, fig_num)

            if (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == True
            ):
                is_micrograph.append(1)
                is_correct.append(1)
                tp_graph += 1
            elif (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == True
            ):
                is_micrograph.append(0)
                is_correct.append(1)
                tn_graph += 1
            elif (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == False
            ):
                is_micrograph.append(0)
                is_correct.append(0)
                fp_graph += 1
            elif (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == False
            ):
                is_micrograph.append(1)
                is_correct.append(0)
                fn_graph += 1
            else:
                raise Exception("ahhhhhhh")

            papers.append(paper)
            fig_nums.append(int(evaluation["figure"]))

            is_micrograph_bool = (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == False
            ) or (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == True
            )
            if eval_all:
                if evaluation["instrument_correct"] and is_micrograph_bool:
                    correct_instrument += 1

                if evaluation["material_correct"] and is_micrograph_bool:
                    correct_mat += 1

            total_n_fig += 1
        total_n_papers += 1
    print(tp_graph, tn_graph, fp_graph, fn_graph)
    print(correct_instrument, correct_instrument / (tp_graph + fn_graph))
    print(correct_mat, correct_mat / (tp_graph + fn_graph))
    return is_micrograph, is_correct, papers, fig_nums


if __name__ == "__main__":
    # get_precision_recall(
    #    "dataset/train/", "gpt3_5_without_abstract", "gpt3_5_without_abstract_eval_auto"
    # )
    gpt_3_5_graph, gpt_3_5_correct, gpt_3_5_papers, gpt_3_5_figs = get_precision_recall(
        "dataset/train/",
        "gpt3_5_with_abstract",
        "gpt3_5_with_abstract_eval",
        eval_all=True,
    )
    gpt_4_graph, gpt_4_correct, gpt_4_papers, gpt_4_figs = get_precision_recall(
        "dataset/train/", "gpt4_with_abstract", "gpt4_with_abstract_eval", eval_all=True
    )

    errors = []
    papers = []
    nums = []
    for i in range(len(gpt_3_5_graph)):
        if gpt_3_5_graph[i] != gpt_4_graph[i]:
            # print(i, gpt_3_5_graph[i], gpt_4_graph[i])
            errors.append(i)
            papers.append(gpt_3_5_papers[i])
            nums.append(gpt_4_figs[i])
    print(len(errors))
    # print(len(set(papers)), len(set(gpt_3_5_papers)))
    unique_papers = list(set(papers))
    with open("possible_errors.txt", "w+") as f:
        for p, n in zip(papers, nums):
            f.writelines(f"{p}  {n}\n")

    # get_precision_recall("dataset/train/", "human", "gpt4_with_abstract_eval")
    # train_test_split("dataset", n_train=1500, filter_term="arxiv")


# w/out abstract: 291 1796 27 93
# w/ abstract 383 1607 110 107
