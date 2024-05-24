from os import listdir, getcwd
from json import load
import csv


paper_data: list[list[str]] = []
ds_path: str = "dataset/vlm_results"
subfig_fname: str = "labels_gpt4_vision_subfigure.json"
metadata_fname: str = "paper_data.json"


def extract_data(path: str) -> dict | None:
    try:
        with open(path, "r") as f:
            data = load(f)
            return data
    except:
        return None


def get_figure_caption(idx: int, caption_data: dict) -> str:
    for fig in caption_data:
        if fig["name"] == str(idx) and fig["figType"] == "Figure":
            return fig["caption"]
    return "missing"


def write_paper_data(paper_data: list[str]) -> None:
    with open("dataset/vlm_results/labels.csv", "w+") as f:
        writer = csv.writer(f, delimiter="|")
        for data in paper_data:
            writer.writerow(data)


# loop through all figures, get data and save to csv. Optionally generate MatSciBERT embeddings
i = 0
for folder in listdir(ds_path):
    if len(folder.split(".")) > 1:  # index spreadsheet
        continue
    subgfigure_data = extract_data(f"{ds_path}/{folder}/{subfig_fname}")
    metadata = extract_data(f"{ds_path}/{folder}/{metadata_fname}")
    captions = extract_data(f"{ds_path}/{folder}/captions.json")
    if subgfigure_data == None or metadata == None or captions == None:  # oopsies!
        continue
    for subgfigure in subgfigure_data:  # type: ignore
        current_subfig_data = []
        if subgfigure["isMicrograph"] == False:
            continue
        else:
            fig_n, subfig_n = subgfigure["figure"], subgfigure["subfigure"]
            new_fname = f"{folder}_fig_{fig_n}_{subfig_fname}"
            caption = get_figure_caption(fig_n, captions)  # type: ignore
            material, comments = subgfigure["material"], ", ".join(
                subgfigure["comments"]
            )
            current_subfig_data = [
                str(i),
                new_fname,
                material,
                subgfigure["instrument"],
                comments,
                caption,
                metadata["title"],  # type: ignore
                ", ".join(metadata["authors"]),  # type: ignore
                metadata["doi"],  # type: ignore
            ]

            paper_data.append(current_subfig_data)
            i += 1
