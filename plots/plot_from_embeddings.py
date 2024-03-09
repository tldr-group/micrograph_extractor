from os import listdir, getcwd
from json import load
import csv
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

np.random.seed(122)
print(getcwd())
import torch
from MatSciBERT.normalize_text import normalize
from transformers import AutoModel, AutoTokenizer

from typing import List, Tuple, TypeAlias, Literal
from dataclasses import dataclass


save_embeddings = False  # True

if save_embeddings:
    tokenizer = AutoTokenizer.from_pretrained("m3rg-iitd/matscibert")
    model = AutoModel.from_pretrained("m3rg-iitd/matscibert")


# Helper functions
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
            if save_embeddings:
                embeddings = get_embeddings(model, [material])  # +  comments
                np.save(f"{ds_path}/{folder}/fig_{fig_n}_{subfig_n}", embeddings)
            paper_data.append(current_subfig_data)
            i += 1

Instrument: TypeAlias = Literal["TEM", "OPTICAL", "SEM", "AFM", "OTHER"]


def get_instrument(suggest_instrument: str) -> Instrument:
    def _check_list(string: str, substrings: List[str]) -> bool:
        match = False
        for sub in substrings:
            if sub in string:
                match = True
        return match

    lower = suggest_instrument.lower()
    if _check_list(lower, ["stem", "scanning transmission electron microscopy"]):
        return "TEM"
    elif _check_list(lower, ["tem", "transmission electron microscopy"]):
        return "TEM"
    elif _check_list(lower, ["optical", "rfm", "reflected light"]):
        return "OPTICAL"
    elif _check_list(lower, ["sem", "scanning electron microscopy"]):
        return "SEM"
    elif _check_list(lower, ["afm", "atomic force microscopy"]):
        return "AFM"
    else:
        return "OTHER"


colours = {
    "TEM": "#65af4b",
    "OPTICAL": "#fed966",
    "SEM": "#82c3ff",
    "AFM": "#ff6666",
    "OTHER": "#7c7c7c",
}


@dataclass
class MaterialImage:
    bert_embedding: np.ndarray
    material: str
    instrument: str
    path: str
    fig_idx: Tuple[int, int]
    size: Tuple[int, int]
    pos: Tuple[float, float]

    def __post_init__(self) -> None:
        self.area = self.size[0] * self.size[1]
        self.uid = self.path.split("/")[2] + "_" + str(self.fig_idx[0])
        self.instrument = get_instrument(self.instrument)


images: List[MaterialImage] = []

# Loop through all figures, get info needed to plot T-SNE (material, instrument, image size)
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
            img_path = f"{ds_path}/{folder}/imgs/captions_fig_{fig_n}_{subfig_n}.jpg"

            embedding = np.load(f"{ds_path}/{folder}/fig_{fig_n}_{subfig_n}.npy")
            mean_embed = np.mean(embedding, axis=1)
            temp_img = Image.open(img_path)
            img = MaterialImage(
                mean_embed,
                subgfigure["material"],
                subgfigure["instrument"],
                img_path,
                (fig_n, subfig_n),
                (temp_img.width, temp_img.height),
                (0, 0),
            )
            temp_img.close()
            images.append(img)

embeddings_np = np.concatenate([i.bert_embedding for i in images])

dim_reduction = TSNE(n_components=2, perplexity=40, early_exaggeration=4)
reduced_dims = dim_reduction.fit_transform(
    embeddings_np,
)

for i, img in enumerate(images):
    img.pos = reduced_dims[i, :]  # type: ignore

plt.figure(figsize=(8, 8))
plt.scatter(reduced_dims[:, 0], reduced_dims[:, 1])
# plt.xlim()
# plt.ylim()
DATA_XRANGE = (
    -110,
    110,
)  # pca, avg (-6, 10) #pca sum (-100, 300) #pca, sum, comments (-300, 450)
DATA_YRANGE = (
    -110,
    110,
)  # pca, avg (-6, 7) #pca, avg (-6, 10) #pca sum (-100, 150) #pca, sum, comments (-200, 250)
CANV_SIZE = (8000, 8000)
BORDER_WIDTH = 8


def radial_rescale(x: int, y: int, max_scale: int = 120) -> Tuple[int, int]:
    dist = np.sqrt(((x) ** 2 + (y) ** 2))
    return dist


def to_canvas_coords(
    data_coord: Tuple[float, float],
    xrange: Tuple[int, int],
    yrange: Tuple[int, int],
    canv_size: Tuple[int, int],
) -> Tuple[int, int]:
    new_x = canv_size[0] * (data_coord[0] - xrange[0]) / (xrange[1] - xrange[0])
    new_y = canv_size[1] * (data_coord[1] - yrange[0]) / (yrange[1] - yrange[0])
    return (int(new_x), int(new_y))


def get_image(mat: MaterialImage) -> Image.Image:
    img = Image.open(mat.path).convert("RGB")
    new_w, new_h = img.width // 2, img.height // 2
    downsample = img.resize((new_w, new_h))
    outline = Image.new("RGB", (new_w + BORDER_WIDTH * 2, new_h + BORDER_WIDTH * 2))
    outline.paste(colours[mat.instrument], (0, 0, outline.width, outline.height))
    outline.paste(downsample, (BORDER_WIDTH, BORDER_WIDTH))
    return outline


images.sort(key=lambda x: x.area, reverse=True)

canvas = Image.new("RGB", CANV_SIZE)
draw = ImageDraw.Draw(canvas)
canvas.paste((255, 255, 255), (0, 0, canvas.width, canvas.height))
for i, mat in enumerate(images):
    ox, oy = mat.pos
    x, y = to_canvas_coords((ox, oy), DATA_XRANGE, DATA_YRANGE, CANV_SIZE)
    outlined_img = get_image(mat)
    canvas.paste(
        outlined_img, (x - outlined_img.width // 2, y - outlined_img.height // 2)
    )


images.sort(key=lambda x: x.area, reverse=False)
ids_label_added = []
font = ImageFont.truetype("/home/ronan/.fonts/arial.ttf", 32)

for i, mat in enumerate(images):
    if mat.uid not in ids_label_added:
        ox, oy = mat.pos
        x, y = to_canvas_coords((ox, oy), DATA_XRANGE, DATA_YRANGE, CANV_SIZE)
        new_w, new_h = (mat.size[0] // 4) + len(mat.material[:25]) * 2, (
            mat.size[1] // 4
        ) + 40
        draw.text((x - new_w, y - new_h), mat.material[:25], fill="#000000", font=font)
        # draw.text((x - new_w, y + new_h), mat.instrument, fill="#000000", font=font)
        ids_label_added.append(mat.uid)

canvas.save("out.png")
