import os
from os import listdir
from json import load, dump
from shutil import copytree, rmtree
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

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
                    labels = load(file)

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
                    dump(labels, file, ensure_ascii=False, indent=4)


def detect_composite_image_from_caption(caption: str) -> bool:
    if "(a)" in caption.lower() or " a. " in caption.lower():
        return True
    else:
        return False


def _check_list(string: str, substrings: List[str]) -> bool:
    match = False
    for sub in substrings:
        if sub in string:
            match = True
    return match


def get_instrument(suggest_instrument: str) -> str:

    lower = suggest_instrument.lower()
    if _check_list(lower, ["eds", "edx", "energy-dispersive"]):
        return "EDX"
    elif _check_list(lower, ["stem", "scanning transmission electron microscopy"]):
        return "STEM"
    elif _check_list(lower, ["tem", "transmission electron microscopy"]):
        return "TEM"
    elif _check_list(lower, ["optical", "rfm", "reflected light"]):
        return "OPTICAL"
    elif _check_list(lower, ["fluorescence", "fluorescence microscopy"]):
        return "FM"
    elif _check_list(lower, ["sem", "scanning electron microscopy"]):
        return "SEM"
    elif _check_list(lower, ["afm", "atomic force microscopy"]):
        return "AFM"
    else:
        return "OTHER"


def get_is_micrograph(caption: str) -> bool:
    lower = caption.lower()
    if _check_list(lower, ["image", "micrograph"]):
        return True
    else:
        return False


def regex_labelling(path: str, greedy: bool = False) -> None:
    for paper in listdir(f"{path}"):

        try:
            with open(f"{path}{paper}/labels.json") as f:
                try:
                    labels_data = load(f)
                except:
                    continue
            with open(f"{path}{paper}/captions.json") as f:
                try:
                    captions_data = load(f)
                except:
                    continue
        except FileNotFoundError:
            continue

        regex_eval = []
        for item in captions_data:
            print(item["figType"])
            if item["figType"] == "Figure":
                caption = item["caption"]
                instrument = get_instrument(caption)
                image_mentioned = get_is_micrograph(caption)
                if greedy:
                    is_micrograph = image_mentioned or instrument != "OTHER"
                else:
                    is_micrograph = image_mentioned
                instrument = "none" if instrument == "OTHER" else instrument
                data = {
                    "figure": item["name"],
                    "isMicrograph": is_micrograph,
                    "instrument": instrument,
                }
                regex_eval.append(data)

        name = "regex_greedy" if greedy else "regex_simple"
        labels_data[f"{name}"] = regex_eval
        with open(f"{path}{paper}/labels.json", "w") as f:
            dump(labels_data, f, ensure_ascii=False, indent=4)


def auto_eval_regex(
    path: str, which: str = "greedy", plot_matrix: bool = False
) -> Tuple:
    results = get_precision_recall(
        path, "gpt4_with_abstract", "gpt4_with_abstract_eval"
    )

    j = 0
    print(len(results[0][2]))
    tp_graph, tn_graph, fp_graph, fn_graph = 0, 0, 0, 0
    correct_instrument = 0

    y_pred = []
    y_true = results[0][1]

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
            labels = data[f"regex_{which}"]
            gpt4_labels = data["gpt4_with_abstract"]
            gpt4_evals = data["gpt4_with_abstract_eval"]
        except KeyError:
            continue

        if len(gpt4_labels) != len(gpt4_evals):
            continue

        for i in range(len(labels)):
            label = labels[i]
            # fig_num = int(label["figure"])
            # we're nnow comparing is_micro to is-micro so diff to other one
            if label["isMicrograph"] == True and y_true[j] == True:
                y_pred.append(1)
                tp_graph += 1
            elif label["isMicrograph"] == False and y_true[j] == False:
                y_pred.append(0)
                tn_graph += 1
            elif label["isMicrograph"] == True and y_true[j] == False:
                y_pred.append(1)
                fp_graph += 1
            elif label["isMicrograph"] == False and y_true[j] == True:
                y_pred.append(0)
                fn_graph += 1
            else:
                raise Exception("Shouldn't be possible")
            j += 1

    if plot_matrix:
        cmap = "Greys" if which == "greedy" else "Purples"
        plot_confusion_matrix(y_pred, y_true, f"{which} regex", cmap)

    print(tp_graph, tn_graph, fp_graph, fn_graph)
    return (tp_graph, tn_graph, fp_graph, fn_graph)


def get_precision_recall(
    path: str,
    which_labels: str = "gpt3_5_with_abstract",
    which_eval: str = "gpt3_5_with_abstract_eval",
    eval_all: bool = False,
) -> Tuple:
    total_n_fig = 0
    total_n_papers = 0
    tp_graph, tn_graph, fp_graph, fn_graph = 0, 0, 0, 0
    correct_instrument = 0
    correct_mat = 0

    pred_micrograph: List[int] = []
    is_micrograph: List[int] = []
    is_correct: List[int] = []

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
            label = labels[i]
            fig_num = int(label["figure"])
            evaluation = get_eval(evals, fig_num)

            if (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == True
            ):
                pred_micrograph.append(1)
                is_micrograph.append(1)
                is_correct.append(1)
                tp_graph += 1
            elif (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == True
            ):
                pred_micrograph.append(0)
                is_micrograph.append(0)
                is_correct.append(1)
                tn_graph += 1
            elif (
                label["isMicrograph"] == True
                and evaluation["isMicrograph_correct"] == False
            ):
                pred_micrograph.append(1)
                is_micrograph.append(0)
                is_correct.append(0)
                fp_graph += 1
            elif (
                label["isMicrograph"] == False
                and evaluation["isMicrograph_correct"] == False
            ):
                pred_micrograph.append(0)
                is_micrograph.append(1)
                is_correct.append(0)
                fn_graph += 1
            else:
                raise Exception("Shouldn't be possible")

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

    return (
        [pred_micrograph, is_micrograph, is_correct],
        [tp_graph, tn_graph, fp_graph, fn_graph],
        [correct_mat, correct_instrument],
        [total_n_fig, total_n_papers],
    )


FONT_DICT = {"fontsize": 26, "font": "Arial"}


def plot_confusion_matrix(y_pred, y_true, title: str, cmap_name: str = "Blues") -> None:
    plt.figure()
    cm_display = ConfusionMatrixDisplay.from_predictions(
        y_true,
        y_pred,
        labels=[0, 1],
        cmap=plt.get_cmap(cmap_name),
        display_labels=["False", "True"],
        text_kw=FONT_DICT,
    )
    cm_display.ax_.set_title(
        title,
        fontdict={"fontsize": 28, "font": "Arial"},
    )

    x_label = "LLM prediction" if "gpt" in title else "Prediction"
    cm_display.ax_.set_ylabel("Ground Truth", fontdict=FONT_DICT)
    cm_display.ax_.set_xlabel(x_label, fontdict=FONT_DICT)
    cm_display.ax_.images[-1].colorbar.ax.tick_params(
        labelsize=FONT_DICT["fontsize"] - 2
    )
    plt.yticks(fontsize=FONT_DICT["fontsize"])
    plt.xticks(fontsize=FONT_DICT["fontsize"])
    # plt.show()
    plt.tight_layout()
    plt.savefig(f"plots/{title}_confusion_matrix.png")


def _get_all_matrices() -> None:
    gpt_3_5_data = get_precision_recall(
        "dataset/train/",
        "gpt3_5_with_abstract",
        "gpt3_5_with_abstract_eval",
        eval_all=True,
    )
    gpt_4_data = get_precision_recall(
        "dataset/train/", "gpt4_with_abstract", "gpt4_with_abstract_eval", eval_all=True
    )

    gpt_3_5_data_no_abstract = get_precision_recall(
        "dataset/train/",
        "gpt3_5_without_abstract",
        "gpt3_5_without_abstract_eval_auto",
        eval_all=False,
    )
    gpt_4_data_no_abstract = get_precision_recall(
        "dataset/train/",
        "gpt4_without_abstract",
        "gpt4_without_abstract_eval_auto",
        eval_all=False,
    )

    data = [gpt_3_5_data, gpt_4_data, gpt_3_5_data_no_abstract, gpt_4_data_no_abstract]
    titles = [
        "GPT3.5 with abstract",
        "GPT4 with abstract",
        "GPT3.5 no abstract",
        "GPT4 no abstract",
    ]
    cmaps = ["Reds", "Blues", "Oranges", "Greens"]

    for i in range(4):
        y_pred, y_true = np.array(data[i][0][0]), np.array(data[i][0][1])

        n_fig = data[i][3][0]
        print(n_fig)
        mat_acc, instrument_acc = data[i][2][0] / np.sum(y_true), data[i][2][
            1
        ] / np.sum(y_true)
        print(mat_acc, instrument_acc)
        plot_confusion_matrix(y_pred, y_true, titles[i], cmaps[i])


def merge_vlm_into_subfig_labels(path: str) -> None:
    for paper in listdir(path):
        try:
            with open(f"{path}{paper}/subfig_labels.json") as f:
                try:
                    subfig_labels = load(f)
                except:
                    continue
        except (FileNotFoundError, NotADirectoryError):
            continue

        try:
            with open(f"{path}{paper}/labels_gpt4_vision_subfigure.json") as f:
                try:
                    vision_labels = load(f)
                except:
                    continue
        except (FileNotFoundError, NotADirectoryError):
            continue

        subfig_labels["gpt_4_vision"] = vision_labels

        try:
            with open(f"{path}{paper}/subfig_labels.json", "w") as f:
                dump(subfig_labels, f, ensure_ascii=False, indent=4)
        except:
            continue


if __name__ == "__main__":
    # get_precision_recall(
    #    "dataset/train/", "gpt3_5_without_abstract", "gpt3_5_without_abstract_eval_auto"
    # )
    # evaluate_labels("dataset/train/", "gpt4_without_abstract")
    # _get_all_matrices()
    # regex_labelling("dataset/train/", True)
    # regex_labelling("dataset/train/", False)
    # auto_eval_regex("dataset/train/", which="simple", plot_matrix=True)

    merge_vlm_into_subfig_labels("dataset/vlm_results/")
