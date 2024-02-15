from os import listdir
from json import load
import csv
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


import torch
from MatSciBERT.normalize_text import normalize
from transformers import AutoModel, AutoTokenizer

from typing import List, Tuple


save_embeddings = True
if save_embeddings:
    tokenizer = AutoTokenizer.from_pretrained("m3rg-iitd/matscibert")
    model = AutoModel.from_pretrained("m3rg-iitd/matscibert")


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


def get_embeddings(model: torch.nn.Module, sentences: List[str]) -> np.ndarray:
    norm_sents = [normalize(s) for s in sentences]
    tokenized_sents = tokenizer(norm_sents)
    tokenized_sents = {k: torch.Tensor(v).long() for k, v in tokenized_sents.items()}
    with torch.no_grad():
        last_hidden_state = model(**tokenized_sents)[0]
    return last_hidden_state.cpu().numpy()


def write_paper_data(paper_data: List[str]) -> None:
    with open("dataset/vlm_results/labels.csv", "w+") as f:
        writer = csv.writer(f, delimiter="|")
        for data in paper_data:
            writer.writerow(data)


# format: idx, path, material, instrument , comments, caption, title, authors, DOI
paper_data: List[List[str]] = []
ds_path: str = "dataset/vlm_results"
subfig_fname: str = "labels_gpt4_vision_subfigure.json"
metadata_fname: str = "paper_data.json"

i = 0
for folder in listdir(ds_path):
    if len(folder.split(".")) > 1:  # index spreadsheet
        continue
    subgfigure_data = extract_data(f"{ds_path}/{folder}/{subfig_fname}")
    metadata = extract_data(f"{ds_path}/{folder}/{metadata_fname}")
    captions = extract_data(f"{ds_path}/{folder}/captions.json")
    if subgfigure_data == None or metadata == None or captions == None:  # oopsies!
        continue
    for subgfigure in subgfigure_data:
        current_subfig_data = []
        if subgfigure["isMicrograph"] == False:
            continue
        else:
            fig_n, subfig_n = subgfigure["figure"], subgfigure["subfigure"]
            new_fname = f"{folder}_fig_{fig_n}_{subfig_fname}"
            caption = get_figure_caption(fig_n, captions)
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
                metadata["title"],
                ", ".join(metadata["authors"]),
                metadata["doi"],
            ]
            if save_embeddings:
                embeddings = get_embeddings(model, [material])  # +  comments
                np.save(f"{ds_path}/{folder}/fig_{fig_n}_{subfig_n}", embeddings)
            paper_data.append(current_subfig_data)
            i += 1

embeddings: List[np.ndarray] = []
instruments: List[str] = []
materials: List[str] = []
img_paths: List[str] = []
fig_idxs: List = []

i = 0
for folder in listdir(ds_path):
    if len(folder.split(".")) > 1:  # index spreadsheet
        continue
    subgfigure_data = extract_data(f"{ds_path}/{folder}/{subfig_fname}")
    metadata = extract_data(f"{ds_path}/{folder}/{metadata_fname}")
    captions = extract_data(f"{ds_path}/{folder}/captions.json")
    if subgfigure_data == None or metadata == None or captions == None:  # oopsies!
        continue
    for subgfigure in subgfigure_data:
        current_subfig_data = []
        if subgfigure["isMicrograph"] == False:
            continue
        else:
            fig_n, subfig_n = subgfigure["figure"], subgfigure["subfigure"]
            embedding = np.load(f"{ds_path}/{folder}/fig_{fig_n}_{subfig_n}.npy")
            sum_embed = np.mean(embedding, axis=1)
            embeddings.append(sum_embed)
            instruments.append(subgfigure["instrument"])
            materials.append(subgfigure["material"])
            img_paths.append(
                f"{ds_path}/{folder}/imgs/captions_fig_{fig_n}_{subfig_n}.jpg"
            )
            # fig_idxs.append((fig_n, subfig_n))

embeddings_np = np.concatenate(embeddings)

pca = TSNE(n_components=2)
embeddings_reduced = pca.fit_transform(embeddings_np)

plt.figure(figsize=(8, 8))
plt.scatter(embeddings_reduced[:, 0], embeddings_reduced[:, 1])
# plt.xlim()
# plt.ylim()

DATA_XRANGE = (
    -120,
    120,
)  # pca, avg (-6, 10) #pca sum (-100, 300) #pca, sum, comments (-300, 450)
DATA_YRANGE = (
    -100,
    100,
)  # pca, avg (-6, 7) #pca, avg (-6, 10) #pca sum (-100, 150) #pca, sum, comments (-200, 250)
CANV_SIZE = (10000, 10000)


def to_canvas_coords(
    data_coord: Tuple[int, int],
    xrange: Tuple[int, int],
    yrange: Tuple[int, int],
    canv_size: Tuple[int, int],
) -> Tuple:
    new_x = canv_size[0] * (data_coord[0] - xrange[0]) / (xrange[1] - xrange[0])
    new_y = canv_size[1] * (data_coord[1] - yrange[0]) / (yrange[1] - yrange[0])
    return (new_x, new_y)


canvas = Image.new("RGB", CANV_SIZE)
canvas.paste((255, 255, 255), (0, 0, canvas.width, canvas.height))
for i in range(len(embeddings)):
    ox, oy = embeddings_reduced[i]
    x, y = to_canvas_coords((ox, oy), DATA_XRANGE, DATA_YRANGE, CANV_SIZE)
    x, y = int(x), int(y)
    material = materials[i]
    img = Image.open(img_paths[i]).convert("RGB")
    new_w, new_h = img.width // 2, img.height // 2
    img = img.resize((new_w, new_h))
    # print(type(img), type(canvas), new_w, new_h)
    canvas.paste(img, (x - new_w // 2, y - new_h // 2))
    # plt.text(x, y, material)

# TODO:
# order images by size, drawing largest first
# draw with coloured border depending on instrument
# cluster and draw text of cluster centroid material

canvas.save("out.png")
