from os import getcwd
from os.path import join
from PIL import Image
import pandas as pd
import numpy as np

np.random.seed(1001)
import matplotlib.pyplot as plt


colours = {
    "TEM": "#65af4b",
    "OPTICAL": "#fed966",
    "SEM": "#82c3ff",
    "AFM": "#ff6666",
    "OTHER": "#7c7c7c",
    "RENDER": "#000000",
}
BORDER_WIDTH = 8


def _check_list(string: str, substrings: list[str]) -> bool:
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


def abbr_fname_to_full(abbr_fname: str) -> str:
    splits = abbr_fname.split("_")
    subfig_n = splits[-1][1:]
    fig_n = splits[-2][1:]
    rest = splits[:-2]
    fname_li = rest + ["fig", fig_n, subfig_n]
    return "_".join(fname_li) + ".jpg"


def load_df(standardise_instruments: bool = True) -> pd.DataFrame:
    cwd = getcwd()
    labels_path = join(cwd, "micrographs/labels.csv")
    df = pd.read_csv(
        labels_path,
        delimiter="|",
    )
    df.columns = [
        "idx",
        "abbreviated_fname",
        "llm_label",
        "instrument",
        "comments",
        "real_caption",
        "title",
        "authors",
        "doi",
    ]
    # remove duplicate index
    df = df.drop(
        columns=["idx"],
    )
    if standardise_instruments:
        df["instrument"] = df["instrument"].apply(get_instrument)

    return df


def get_image(
    mat: Image.Image, instrument: str, sf: float = 0.5, bw: int = BORDER_WIDTH
) -> Image.Image:
    img = mat.convert("RGB")
    new_w, new_h = int(img.width * sf), int(img.height * sf)
    downsample = img.resize((new_w, new_h))
    outline = Image.new("RGB", (new_w + bw * 2, new_h + bw * 2))
    outline.paste(colours[instrument], (0, 0, outline.width, outline.height))
    outline.paste(downsample, (bw, bw))
    return outline


def resize_longest_side(img: Image.Image, l: int, patch_size: int = 14) -> Image.Image:
    oldh, oldw = img.height, img.width
    scale = l * 1.0 / max(oldh, oldw)
    newh, neww = oldh * scale, oldw * scale
    neww = int(neww + 0.5)
    newh = int(newh + 0.5)
    neww = neww - (neww % patch_size)
    newh = newh - (newh % patch_size)

    return img.resize((neww, newh))


def entry_to_text(row: pd.DataFrame) -> str:
    mat_key = "Material"
    llm_label = row["llm_label"].iloc[0]
    instrument = row["instrument"].iloc[0]
    comments = row["comments"].iloc[0]

    fmt_comments = "\n".join([f"* {cmt}" for cmt in comments.split(", ")])
    out_str = "\n".join(
        [
            f"{mat_key}: {llm_label}",
            f"Instrument: {instrument}",
            f"Comments: \n{fmt_comments}",
        ]
    )
    return out_str


if __name__ == "__main__":
    CWD = getcwd()
    df = load_df(True)

    sem_micrographs = df[df["instrument"] == "SEM"]
    tem_micrographs = df[df["instrument"] == "TEM"]
    optical_micrographs = df[df["instrument"] == "OPTICAL"]

    rows = []
    for df in [sem_micrographs, tem_micrographs, optical_micrographs]:
        row = df.sample(1)
        print(abbr_fname_to_full(row["abbreviated_fname"].iloc[0]))
        rows.append(row)

    fig, axs = plt.subplots(nrows=3, ncols=2)
    fig.set_size_inches(10, 10)

    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

    for i, row in enumerate(rows):
        fname = abbr_fname_to_full(row["abbreviated_fname"].iloc[0])

        img_path = join(CWD, "micrographs", fname)
        img = Image.open(img_path)
        img = resize_longest_side(img, 512 * 2, 1)
        img = get_image(img, row["instrument"].iloc[0])
        axs[i, 0].imshow(img)
        axs[i, 0].set_axis_off()

        text = entry_to_text(row)
        axs[i, 1].text(
            0,
            0.5,
            fontsize=12,
            s=text,
            color="r",
            bbox=props,
            fontfamily="monospace",
            wrap=True,
        )

        caption_text = row["real_caption"].iloc[0][:500]
        caption_text_fmt = f'"{caption_text}..."'
        axs[i, 1].text(0, 0.1, fontsize=9, s=caption_text_fmt, wrap=True)
        axs[i, 1].set_axis_off()

    plt.tight_layout()
    plt.savefig("plots/supp_labels.png")
