import subprocess
import numpy as np
from PIL import Image
from skimage.measure import label
from skimage.morphology import binary_opening
from os import getcwd
from typing import List, Tuple

CWD = getcwd()
PDFF2_PATH: str = f"{CWD}/pdffigures2/"
PDFF2_CMD: str = "runMain org.allenai.pdffigures2.FigureExtractorBatchCli"
TEST_PDF_PATH: str = f"{CWD}/data/"
TEST_IMG_PATH: str = f"{CWD}/outputs/imgs/"
TEST_DATA_PATH: str = f"{CWD}/outputs/data/"


def extract_figures_captions(
    abs_read_path: str,
    abs_img_save_path: str,
    abs_caption_save_path: str,
    DPI: int = 200,
    verbose: bool = False,
    continue_on_err: bool = True,
) -> int:
    """Run pdffigures2 (https://github.com/allenai/pdffigures2) on pdf file/directory, saving output figures and captions to given directory.

    Output img name: <paper_filename>-<figure_name>-1.<filetype>
    i.e p0-Figure1-1.png

    Output data name: <paper_filename>.json
    i.e p0.json
    The .json contains captions for each figure, under the "caption" key and which figure it corresponds to in the "renderURL" key (full path
    to the figure)

    :param abs_read_path: absolute file path/directory to read pdfs from
    :type abs_read_path: str
    :param abs_img_save_path: absolute file directory to save figures to
    :type abs_img_save_path: str
    :param abs_caption_save_path: absolute file directory to save metadata + captions to
    :type abs_caption_save_path: str
    :param DPI: DPI of the figures, defaults to 200
    :type DPI: int, optional
    :param continue_on_err: whether pdffigures2 will continue if encounters an error, defaults to True
    :type continue_on_err: bool, optional
    :return: exit code, 0 for success, 1 for failure
    :rtype: int
    """
    run_str: str = f"{PDFF2_CMD} {abs_read_path} -m {abs_img_save_path} -d {abs_caption_save_path} -i {DPI} "
    # close the quotation marks that form the sbt argument, either with command to ignore errors or just a quotation mark
    if continue_on_err is True:
        run_str += "-e "
    stdout = subprocess.STDOUT
    if verbose is False:
        stdout = subprocess.DEVNULL

    exit_code: int = 0
    try:
        subprocess.run(["sbt", run_str], check=True, cwd=PDFF2_PATH, stdout=stdout)
    except subprocess.CalledProcessError as err:
        exit_code = 1
    return exit_code


WHITE_CUTOFF: int = 250  # pixel value to treat as white i.e bg
AREA_CUTOFF: int = 100 * 100  # smallest figure size
OFFSETS = [(3, 3), (-3, -3)]


def arr_to_img(arr: np.ndarray, mode="RGB") -> Image.Image:
    return Image.fromarray(arr, mode=mode)


def img_to_arr(img: Image.Image, mode="RGB") -> np.ndarray:
    return np.array(img.convert(mode))


def get_bbox(
    arr: np.ndarray, offsets: List[Tuple[int, int]] = [(0, 0), (0, 0)]
) -> List[int]:
    """Get bbox of binary arr by looking at min/max x/y.

    :param arr: binary array shape (h, w)
    :type arr: np.ndarray
    :param offsets: bbox offsets (if img cropped), defaults to (0, 0)
    :type offsets: Tuple[int, int], optional
    :return: bbox in form x0 y0 x1 y1
    :rtype: List[int]
    """
    idxs = np.nonzero(arr)
    y_min, y_max = np.amin(idxs[0]), np.amax(idxs[0])
    x_min, x_max = np.amin(idxs[1]), np.amax(idxs[1])

    ox0, oy0 = offsets[0]
    ox1, oy1 = offsets[1]
    x0, y0 = int(x_min + ox0), int(y_min + oy0)  # type: ignore
    x1, y1 = int(x_max + ox1), int(y_max + oy1)  # type: ignore
    return [x0, y0, x1, y1]


def binarize_img(greyscale_figure_arr: np.ndarray, cutoff_val: int) -> np.ndarray:
    binary_arr = np.where(greyscale_figure_arr < cutoff_val, 1, 0)
    opened = binary_opening(binary_arr)
    return opened


def check_area_from_bbox(bbox: List[int], area_cutoff: int) -> bool:
    x0, y0, x1, y1 = bbox
    area = (y1 - y0) * (x1 - x0)
    if area > area_cutoff:
        return True
    else:
        return False


def get_subimage_bboxes(greyscale_figure_arr: np.ndarray) -> List[List[int]]:
    binary_arr = binarize_img(greyscale_figure_arr, WHITE_CUTOFF)
    labelled_arr, n_subimages = label(binary_arr, return_num=True)  # type: ignore
    bboxes: List[List[int]] = []
    for i in range(1, n_subimages + 1):
        current_mask = np.where(labelled_arr == i, 1, 0)
        bbox = get_bbox(current_mask, OFFSETS)
        is_valid = check_area_from_bbox(bbox, AREA_CUTOFF)
        if is_valid:
            bboxes.append(bbox)
    return bboxes


def split_composite_figure(figure: Image.Image) -> List[np.ndarray]:
    rgb_arr = img_to_arr(figure)
    greyscale_arr = img_to_arr(figure, "L")
    bboxes = get_subimage_bboxes(greyscale_arr)
    out_img_arrs = []
    for bbox in bboxes:
        x0, y0, x1, y1 = bbox
        current_subimg = rgb_arr[y0:y1, x0:x1, :]
        out_img_arrs.append(current_subimg)
    return out_img_arrs


if __name__ == "__main__":
    img = Image.open(f"{TEST_IMG_PATH}/p0-Figure1-1.png").convert("L")
    arr = img_to_arr(img, "L")
    print(arr.shape, arr.dtype)
    print(np.amax(arr), np.amin(arr))
    split_arrs = split_composite_figure(img)
    for i, arr in enumerate(split_arrs):
        img = arr_to_img(arr, "RGB")
        img.save(f"{i}.png")
