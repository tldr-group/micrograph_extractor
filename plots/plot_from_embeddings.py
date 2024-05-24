from os import mkdir, getcwd
from os.path import join
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

from typing import TypeAlias, Literal
from dataclasses import dataclass

from plot_llm_labels import colours, load_df, get_image, abbr_fname_to_full


save_embeddings = False  # True

if save_embeddings:
    tokenizer = AutoTokenizer.from_pretrained("m3rg-iitd/matscibert")
    model = AutoModel.from_pretrained("m3rg-iitd/matscibert")


def get_embeddings(model: torch.nn.Module, sentences: list[str]) -> np.ndarray:
    norm_sents = [normalize(s) for s in sentences]
    tokenized_sents = tokenizer(norm_sents)
    tokenized_sents = {k: torch.Tensor(v).long() for k, v in tokenized_sents.items()}
    with torch.no_grad():
        last_hidden_state = model(**tokenized_sents)[0]
    return last_hidden_state.cpu().numpy()


def radial_rescale(x: int, y: int, max_scale: int = 120) -> tuple[int, int]:
    dist = np.sqrt(((x) ** 2 + (y) ** 2))
    return dist


def to_canvas_coords(
    data_coord: tuple[float, float],
    xrange: tuple[int, int],
    yrange: tuple[int, int],
    canv_size: tuple[int, int],
) -> tuple[int, int]:
    new_x = canv_size[0] * (data_coord[0] - xrange[0]) / (xrange[1] - xrange[0])
    new_y = canv_size[1] * (data_coord[1] - yrange[0]) / (yrange[1] - yrange[0])
    return (int(new_x), int(new_y))


CWD = getcwd()
df = load_df(True)
# Optionally generate MatSciBERT embeddings

if save_embeddings:
    try:
        embeddings_path = join(CWD, "plots/embeddings")
        mkdir(embeddings_path)
    except FileExistsError:
        pass

    for i in range(len(df)):
        obj = df.iloc[i]
        name = obj["abbreviated_fname"]
        material = obj["llm_label"]
        save_path = join(embeddings_path, f"{name}.npy")
        embeddings = get_embeddings(model, [material])  # +  comments
        np.save(save_path, embeddings)


Instrument: TypeAlias = Literal["TEM", "OPTICAL", "SEM", "AFM", "OTHER"]


@dataclass
class MaterialImage:
    bert_embedding: np.ndarray
    material: str
    instrument: str
    path: str
    uid: str
    fig_subfig: tuple[int, int]
    size: tuple[int, int]
    pos: tuple[float, float]

    def __post_init__(self) -> None:
        self.area = self.size[0] * self.size[1]


def check_corners(
    img: Image.Image, x: int, y: int, bbox: tuple[int, int, int, int]
) -> bool:
    mw, mh = img.width // 2, img.height // 2
    corners = [(x - mw, y - mh), (x - mw, y + mh), (x + mw, y + mh), (x + mw, y - mh)]
    bx0, by0, bx1, by1 = bbox
    for cx, cy in corners:
        if (bx0 < cx) and (cx < bx1) and (by0 < cy) and (cy < by1):
            return True
    return False


def remap_insturment(instrument: str) -> str:
    if instrument == "FM":
        return "OTHER"
    elif instrument == "EDX":
        return "OTHER"
    elif instrument == "STEM":
        return "TEM"
    else:
        return instrument


images: list[MaterialImage] = []
for i in range(len(df)):
    obj = df.iloc[i]
    material, instrument, abbrv = (
        obj["llm_label"],
        obj["instrument"],
        obj["abbreviated_fname"],
    )
    instrument = remap_insturment(instrument)
    embeddings_path = join(CWD, "plots/embeddings")
    load_path = join(embeddings_path, f"{abbrv}.npy")
    embedding = np.load(load_path)
    mean_embed = np.mean(embedding, axis=1)

    li = abbrv.split("_")
    fig, subfig = int(li[-2][1:]), int(li[-1][1:])
    uid = "_".join(li[:-2] + [str(fig)])
    fname = abbr_fname_to_full(abbrv)
    img_path = join(CWD, "micrographs", fname)

    temp_img = Image.open(img_path)
    img = MaterialImage(
        mean_embed,
        material,
        instrument,
        img_path,
        uid,
        (fig, subfig),
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


images.sort(key=lambda x: x.area, reverse=True)

canvas = Image.new("RGB", CANV_SIZE)
draw = ImageDraw.Draw(canvas)
canvas.paste((255, 255, 255), (0, 0, canvas.width, canvas.height))

inset_data_coords = (3000, 3300, 3800, 4350)
idx0, idy0, idx1, idy1 = inset_data_coords

inset_img = Image.new("RGB", (2 * (idx1 - idx0), 2 * (idy1 - idy0)))
draw_inset = ImageDraw.Draw(inset_img)
inset_img.paste((255, 255, 255), (0, 0, inset_img.width, inset_img.height))


for i, mat in enumerate(images):
    ox, oy = mat.pos
    x, y = to_canvas_coords((ox, oy), DATA_XRANGE, DATA_YRANGE, CANV_SIZE)
    # if x, y in inset data coords, draw onto inset
    temp_img = Image.open(mat.path)
    outlined_img = get_image(temp_img, mat.instrument)
    temp_img.close()
    cx, cy = (x - outlined_img.width // 2, y - outlined_img.height // 2)
    canvas.paste(outlined_img, (cx, cy))

    # todo: check if any corner of the thumbnail sits in this region
    if check_corners(outlined_img, x, y, inset_data_coords):
        temp_img = Image.open(mat.path)
        outlined_img = get_image(temp_img, mat.instrument, 1)
        temp_img.close()
        nx, ny = (2 * (x - idx0) - outlined_img.width // 2), (
            2 * (y - idy0) - outlined_img.height // 2
        )
        inset_img.paste(outlined_img, (nx, ny))


images.sort(key=lambda x: x.area, reverse=False)
ids_label_added = []
font = ImageFont.truetype("/home/ronan/.fonts/arial.ttf", 32)
inset_font = ImageFont.truetype("/home/ronan/.fonts/arial.ttf", 64)
# add text
for i, mat in enumerate(images):
    if mat.uid not in ids_label_added:
        ox, oy = mat.pos
        x, y = to_canvas_coords((ox, oy), DATA_XRANGE, DATA_YRANGE, CANV_SIZE)
        new_w, new_h = (mat.size[0] // 4) + len(mat.material[:25]) * 2, (
            mat.size[1] // 4
        ) + 40
        draw.text((x - new_w, y - new_h), mat.material[:25], fill="#000000", font=font)
        ids_label_added.append(mat.uid)

        if check_corners(outlined_img, x, y, inset_data_coords):
            new_w, new_h = (mat.size[0] // 2) + len(mat.material[:25]) * 2, (
                mat.size[1] // 2
            ) + 80
            draw_inset.text(
                (2 * (x - idx0) - new_w, 2 * (y - idy0) - new_h),
                mat.material[:25],
                fill="#000000",
                font=inset_font,
            )


s_lw = 16
draw.rectangle(inset_data_coords, fill=None, outline="#000000", width=s_lw)
inset_img_bordered = get_image(inset_img, "RENDER", 1.67, 20)
print(inset_img_bordered.height, inset_img_bordered.width)


ix0, iy0 = 4000, 4000

draw.line(
    (
        idx0 + s_lw / 2,
        idy1 - s_lw / 2,
        ix0,
        iy0 + inset_img_bordered.height + s_lw / 2 - s_lw / 2,
    ),
    fill="#000000",
    width=16,
)
draw.line(
    (
        idx1 - s_lw / 2,
        idy0 + s_lw / 2,
        ix0 + inset_img_bordered.width - s_lw / 2,
        iy0,
    ),
    fill="#000000",
    width=16,
)
canvas.paste(
    inset_img_bordered,
    [ix0, iy0],
)


canvas.save("out.png")
inset_img.save("inset.png")
