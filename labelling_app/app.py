import json
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
from tkinter import filedialog as fd
from os import listdir
from json import load, dump
from time import sleep, time
from shutil import copyfile

from typing import Literal, Tuple, List

import re

# problem - if it's not split model says not micrograph - need to relabel?

FONT = ("", 14)
LARGER_FONT = ("", 16)
HALF_W = 700
MAX_IMG_D = int(HALF_W * 0.7)
PADX = (20, 20)
PADY = (10, 10)


def open_file_dialog_return_fps(
    title: str = "Pick folder",
) -> Literal[""] | str:
    """Open file dialog and select n files, returning their file paths then loading them."""
    filepaths: Literal[""] | str = fd.askdirectory(title=title)

    if filepaths == ():  # if user closed file manager w/out selecting
        return ""
    return filepaths


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        data = load(f)
    return data


def save_json(path: str, data: dict | List[dict]) -> None:
    with open(path, "w+") as f:
        dump(data, f, ensure_ascii=False, indent=4)


def get_caption(all_captions: List[dict], idx: int) -> str:
    """Given the list of all caption dicts and a desired figure number (1-indexed), return caption associated
    with that figure. We need to loop through every dictionary as the list of dicts aren't in order. Each
    figure dict has a 'name' field that is usually equal to the figure's number, i.e for Figure 1 the 'name'
    field is '1'

    :param all_captions: list of figure dicts from pdffigures2
    :type all_captions: List[dict]
    :param idx: desired figure idx
    :type idx: int
    :return: caption for Figure $idx
    :rtype: str
    """
    for caption_dict in all_captions:
        try:
            fig_type = caption_dict["figType"]
        except KeyError:
            return "not found"

        if fig_type == "Figure":
            try:
                fig_idx = int(caption_dict["name"])
            except ValueError:
                return "not found"

            if fig_idx == idx:
                return caption_dict["caption"]
    return "not found"


def get_fig_and_subfig_n(img_path: str) -> Tuple[int, int]:
    fig_n, subfig_and_suffix = img_path.split("_")[-2:]
    sufig_n = subfig_and_suffix.split(".")[0]
    return (int(fig_n), int(sufig_n))


def get_fig_subfig_n(path: str) -> Tuple[int, int]:
    return (int(path.split("_")[-2]), int(path.split("_")[-1].split(".")[0]))


def get_only_figures(img_paths: List[str], subfigures: bool = False) -> List[str]:
    out_paths = []
    for path in img_paths:
        n_underscore = path.count("_")
        if n_underscore == 2 and subfigures is False:
            val = int(path.split("_")[-1].split(".")[0])
            out_paths.append((path, val))
        elif n_underscore == 3 and subfigures is True:
            f_n, s_n = get_fig_and_subfig_n(path)
            out_paths.append((path, f_n, s_n))
        else:
            pass

    if subfigures:
        correct_order = sorted(out_paths, key=lambda x: (x[1], x[2]))
    else:
        correct_order = sorted(out_paths, key=lambda x: x[1])
    paths = [x[0] for x in correct_order]
    return paths


def sort_human(l):
    # user Julian (https://stackoverflow.com/questions/3426108/how-to-sort-a-list-of-strings-numerically)
    # not working
    convert = lambda text: float(text) if text.isdigit() else text
    alphanum = lambda key: [convert(c) for c in re.split("([-+]?[0-9]*\.?[0-9]*)", key)]
    l.sort(key=alphanum)
    return l


def get_paths_missing_labels() -> List[str]:
    paths = []
    missing_labels_count = 0
    for path in listdir("dataset/train"):
        try:
            with open(f"dataset/train/{path}/labels.json") as f:
                try:
                    data = load(f)
                except:
                    continue
        except FileNotFoundError:
            continue
        if "human" not in data:
            missing_labels_count += 1
            paths.append(path)
    print(missing_labels_count)
    return paths


def get_paths_missing_eval() -> List[str]:
    paths = []
    missing_evals_count = 0
    for path in listdir("dataset/vlm_results"):
        try:
            with open(f"dataset/vlm_results/{path}/subfig_labels.json") as f:
                try:
                    data = load(f)
                except:
                    continue
        except NotADirectoryError:
            pass
        except FileNotFoundError:
            missing_evals_count += 1
            paths.append(path)
            continue

        missing_eval = True
        for key in data.keys():
            if "gpt4_with_abstract_eval" in key:
                missing_eval = False
        if missing_eval == True:
            paths.append(path)
            missing_evals_count += 1
    print(missing_evals_count)
    return paths


InputTypes = Literal["checkbox", "dropdown", "entry", "comment"]
LabelTypes = Literal["none", "human", "llm", "regex"]


class InputField(ttk.Frame):
    def __init__(
        self,
        parent: ttk.LabelFrame,
        text: str,
        entry_type: InputTypes,
    ) -> None:
        # TODO: add second duplicate entry box that we set to compare labels
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.entry_type: InputTypes = entry_type

        label = tk.Label(self, text=text, font=LARGER_FONT)
        label.grid(row=0, column=0, sticky="w")

        self.entry, self.var = self.get_entry_widget_and_var(entry_type)
        self.entry.grid(row=0, column=1, sticky="ew")

        self.compare_entry, self.compare_var = self.get_entry_widget_and_var(entry_type)
        self.compare_entry["state"] = tk.DISABLED

        self.correct_var = tk.BooleanVar(value=True)
        self.correct_box = tk.Checkbutton(
            self, variable=self.correct_var, state=tk.DISABLED
        )

        self.evaluate_mode = False

        if entry_type == "comment":
            self.add_btn = tk.Button(self, text="Add")
            self.add_btn.grid(row=0, column=2, sticky="e")
            # self.correct_box.grid(row=0, column=3, sticky="e")
        # else:
        # self.correct_box.grid(row=0, column=2, sticky="e")

    def get_entry_widget_and_var(
        self, entry_type: InputTypes
    ) -> Tuple[tk.Widget, tk.Variable]:
        var: tk.Variable
        if entry_type == "entry" or entry_type == "comment":
            var = tk.StringVar(self, value="")
            return tk.Entry(self, font=LARGER_FONT, textvariable=var), var
        elif entry_type == "dropdown":
            var = tk.StringVar(self, value="SEM")
            return (
                ttk.Combobox(
                    self,
                    values=[
                        "SEM",
                        "TEM",
                        "AFM",
                        "STEM",
                        "XCT",
                        "Optical",
                        "Reflected Light",
                        "Other (type in box)",
                    ],
                    font=LARGER_FONT,
                    textvariable=var,
                ),
                var,
            )
        else:
            var = tk.BooleanVar(self)
            return (
                tk.Checkbutton(
                    self,
                    text="Yes",
                    font=LARGER_FONT,
                    variable=var,
                ),
                var,
            )

    def reset(self) -> None:
        if self.entry_type == "checkbox":
            self.var.set(False)
            self.compare_var.set(False)
        else:
            self.var.set("")
            self.compare_var.set("")
        self.correct_var.set(True)

    def set_value(self, value: str | bool, idx: int = 0) -> None:
        if idx == 0:
            self.var.set(value)  # type: ignore
        else:
            self.compare_var.set(value)

    def get_value(self, idx: int = 0) -> str | bool:
        var: tk.Variable
        if idx == 0:
            var = self.var
        elif idx == 1:
            var = self.compare_var
        elif idx == 2:
            var = self.correct_var

        if self.entry_type == "checkbox" or idx == 2:
            return bool(var.get())
        else:
            return str(var.get())

    def get(self) -> str | bool:
        return self.get_value()

    def set_evaluate(self, value: bool) -> None:
        self.evaluate_mode = value
        if self.evaluate_mode == True:
            self.entry["state"] = tk.NORMAL
            self.compare_entry["state"] = tk.NORMAL
            self.correct_box["state"] = tk.NORMAL
            self.compare_entry.grid(row=0, column=2)
            self.correct_box.grid(row=0, column=3)
        else:
            self.entry["state"] = tk.NORMAL
            self.correct_box["state"] = tk.DISABLED
            self.compare_entry.grid_forget()
            self.correct_box.grid_forget()


class App(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        ttk.Frame.__init__(self)

        self.root = root
        self.root.geometry(f"{2*HALF_W}x{2*HALF_W}")
        self.root.bind("<Return>", self._enter_pressed)
        self.root.bind("`", self.toggle_full_img)

        self.pack_widgets()
        self.intro_modal()
        self.dir: str
        self.start: int
        self.n: int
        self.label_mode: LabelTypes = "none"
        self.label_subfigs: bool = True
        self.show_full: bool = False

        self.paper_idx: int = 0
        self.figure_idx: int = 0
        self.total_figures: int = 0

        self.paper_paths: List[str] = []
        self.fig_comments: List[str] = []

        self.only_missing = False

        self.current_paper_data: List[dict] = []
        self.current_paper_eval: List[dict] = []

        self.start_t = time()

        # self.switch_to_evaluate()

    # TODO: add keyborad hotkey to show full image in subfigure label mode

    def _set_folder(self) -> None:
        self.dir = open_file_dialog_return_fps()

    def _window_confirm(self) -> None:
        self.start = int(self.start_idx.get())
        self.n = int(self.n_papers.get())
        self.window.destroy()
        self.start_logic(self.dir, self.start, self.n, self.only_missing)

    def start_logic(
        self, folder: str, start_idx: int, n_papers: int, only_missing: bool = False
    ) -> None:
        all_papers = listdir(folder)
        self.paper_paths = all_papers[start_idx : start_idx + n_papers]
        if only_missing:
            self.paper_paths = get_paths_missing_eval()  # get_paths_missing_labels()
        self.n = len(self.paper_paths)
        self.load_paper(self.paper_paths[0])

    def remap_captions_fig_nums(
        self, img_paths: List[str], captions: List[str], fig_nums: List[str]
    ) -> None:
        new_captions, new_fig_nums = [], []
        for path in img_paths:
            f_n = path.split("_")[-2]
            f_n_idx = fig_nums.index(f_n)
            new_captions.append(captions[f_n_idx])
            new_fig_nums.append(f_n)
        self.captions = new_captions
        self.figure_nums = new_fig_nums

    def load_paper(self, path: str) -> None:
        print(path)
        metadata_path = f"{self.dir}/{path}/paper_data.json"
        captions_path = f"{self.dir}/{path}/captions.json"
        imgs_path = f"{self.dir}/{path}/imgs"

        self.metadata = load_json(metadata_path)
        self.title_text_var.set(self.metadata["title"])
        self.abstract_text_var.set(self.metadata["abstract"])

        self.captions, self.figure_nums = self.load_captions(captions_path)
        self.img_paths = get_only_figures(listdir(imgs_path), self.label_subfigs)
        if self.label_subfigs:
            # remap captions and figures to extend to number of subfigures
            self.remap_captions_fig_nums(
                self.img_paths, self.captions, self.figure_nums
            )
            self.caption_text_var.set(self.captions[0])
        print(self.img_paths)
        if len(imgs_path) == 0:
            print("No imgs!")
            self.new_paper()
        self.total_figures = len(self.img_paths)

        self.load_img(f"{self.dir}/{path}/imgs/{self.img_paths[0]}")

    def load_captions(self, captions_path: str) -> Tuple[List[str], List[str]]:
        captions_dict: List[dict] = load_json(captions_path)  # type: ignore

        valid_figures: List[dict] = filter(
            lambda x: x["figType"] == "Figure", captions_dict
        )
        figure_dict = sorted(valid_figures, key=lambda x: int(x["name"]))
        figure_nums = list(map(lambda x: x["name"], figure_dict))
        captions = list(map(lambda x: x["caption"], figure_dict))

        print(figure_nums)
        self.caption_text_var.set(captions[0])
        return captions, figure_nums

    def get_full_img_path(self, n: int) -> str:
        path = self.paper_paths[self.paper_idx]
        return f"{self.dir}/{path}/imgs/{self.img_paths[n]}"

    def load_img(self, img_path: str) -> None:
        img = Image.open(img_path)
        h, w = img.height, img.width
        m_d = max(h, w)
        sf = MAX_IMG_D / m_d
        nh, nw = int(h * sf), int(w * sf)
        img = img.resize((nw, nh))

        self.photo_img = ImageTk.PhotoImage(img)
        self.img.configure(image=self.photo_img)

    def toggle_full_img(self, event=None) -> None:
        # get full path name from subfigure path, show w/ load img
        # else show w/ load img
        if self.show_full is False and self.label_subfigs is True:
            self.show_full = True
            path, ext = self.img_paths[self.figure_idx].split(".")
            print(path)
            last_idx = path.rfind("_")
            new_path = path[:last_idx] + f".{ext}"
            self.load_img(
                f"{self.dir}/{self.paper_paths[self.paper_idx]}/imgs/{new_path}"
            )
        elif self.show_full is True and self.label_subfigs is True:
            self.show_full = False
            self.load_img(
                f"{self.dir}/{self.paper_paths[self.paper_idx]}/imgs/{self.img_paths[self.figure_idx]}"
            )
        else:
            pass

    def add_pressed(self) -> None:
        comment: str = str(self.comments.get())
        self.fig_comments.append(comment)
        self.comments.reset()

    def _enter_pressed(self, event=None) -> None:
        self.confirm_pressed()

    def _view_select_change(self, event) -> None:
        self.label_mode = self.switch_dropdown.get()
        self.switch_to_evaluate(self.label_mode)

    def add_label(self) -> None:
        is_micrograph = self.micrograph.get()

        new_t = time()
        data: dict
        # should i just get subfig n from img_path instead?
        _, subfig_n = get_fig_subfig_n(self.img_paths[self.figure_idx])
        subfig_n = "0" if self.label_subfigs == False else str(subfig_n)

        try:
            if not is_micrograph:
                data = {
                    "figure": self.figure_nums[self.figure_idx],
                    "subfigure": subfig_n,
                    "isMicrograph": is_micrograph,
                    "instrument": "none",
                    "material": "none",
                    "time": new_t - self.start_t,
                }
            else:
                data = {
                    "figure": self.figure_nums[self.figure_idx],
                    "subfigure": subfig_n,
                    "isMicrograph": is_micrograph,
                    "instrument": self.instrument.get(),
                    "material": self.material.get(),
                    "comments": self.fig_comments,
                    "time": new_t - self.start_t,
                }
            self.current_paper_data.append(data)
        except:
            pass

    def add_eval(self) -> None:
        _, subfig_n = get_fig_subfig_n(self.img_paths[self.figure_idx])
        subfig_n = "0" if self.label_subfigs == False else str(subfig_n)
        data = {
            "figure": self.figure_nums[self.figure_idx],
            "subfigure": subfig_n,
            "isMicrograph_correct": self.micrograph.get_value(2),
            "instrument_correct": self.instrument.get_value(2),
            "material_correct": self.material.get_value(2),
        }
        self.current_paper_eval.append(data)

    def confirm_pressed(self) -> None:
        # fig, subfig = get_fig_and_subfig_n(self.img_paths[self.figure_idx])

        if self.label_mode == "none":
            self.add_label()
        else:
            self.add_eval()

        self.fig_comments = []

        self.figure_idx += 1
        self.start_t = time()
        print(f"Figure [{self.figure_idx} / {self.total_figures}]")

        # if we're in subfig mode, img paths wont match captions

        if self.figure_idx >= self.total_figures:
            self.reset_gui()
            self.new_paper()
        else:
            caption_idx = self.figure_idx
            self.caption_text_var.set(self.captions[caption_idx])
            try:
                self.load_img(self.get_full_img_path(self.figure_idx))
            except FileNotFoundError:
                self.confirm_pressed()

            self.reset_gui()

            if self.label_mode != "none":
                self.switch_to_evaluate(self.label_mode)

    def reset_gui(self) -> None:
        self.micrograph.set_value(False)
        self.instrument.set_value("SEM")
        self.micrograph.set_value(False, 1)
        self.instrument.set_value("SEM", 1)
        self.material.reset()
        self.comments.reset()

    def save_labels(
        self, data: dict, path: str, fname: str = "labels", key: str = "human"
    ) -> None:
        if self.label_subfigs:
            fname = "subfig_" + fname

        try:
            with open(f"{self.dir}/{path}/{fname}.json", "r") as f:
                prev_data = load(f)
        except FileNotFoundError:
            prev_data = {}
        prev_data[key] = data
        save_json(f"{self.dir}/{path}/{fname}.json", prev_data)

    def new_paper(self) -> None:
        sleep(0.25)
        path = self.paper_paths[self.paper_idx]
        if self.label_mode == "none":
            self.save_labels(self.current_paper_data, path)
        else:
            self.save_labels(
                self.current_paper_eval, path, key=self.label_mode + "_eval"
            )

        print(
            f"Paper {self.start + self.paper_idx}, {self.paper_idx / self.n:.3f}% done"
        )
        self.paper_idx += 1
        self.figure_idx = 0
        new_path = self.paper_paths[self.paper_idx]
        self.current_paper_data = []
        self.current_paper_eval = []
        self.load_paper(new_path)
        if self.label_mode != "none":
            self.switch_to_evaluate(self.label_mode)

    def switch_to_evaluate(self, label_type: LabelTypes) -> None:
        self.label_mode = label_type
        if label_type == "none":
            for i, e in enumerate(self.entries):
                e.set_evaluate(False)
            return

        human_label_data = self.load_label_data(
            "human", self.paper_paths[self.paper_idx]
        )
        # TODO: adapt this for subfigure mode
        current_figure_number = human_label_data[self.figure_idx]["figure"]

        all_label_data = self.load_label_data(
            label_type, self.paper_paths[self.paper_idx]
        )
        print(all_label_data)
        print(human_label_data)
        print(self.figure_nums)

        fig_label_data = all_label_data.get(str(current_figure_number))

        if fig_label_data is None:
            print(
                f"No matching label data found for figure {current_figure_number} in {label_type}"
            )

        data = [
            fig_label_data.get("isMicrograph"),
            fig_label_data.get("instrument", "none"),
            fig_label_data.get("material", "none"),
        ]

        for i, e in enumerate(self.entries):
            e.set_evaluate(True)
            if i < 3:
                e.set_value(data[i], 1)

        all_label_data = self.load_label_data("human", self.paper_paths[self.paper_idx])
        fig_label_data = all_label_data[self.figure_idx]
        data = [
            fig_label_data["isMicrograph"],
            fig_label_data["instrument"],
            fig_label_data["material"],
        ]
        for i, e in enumerate(self.entries):
            e.set_evaluate(True)
            if i < 3:
                e.set_value(data[i], 0)

    def load_label_data(
        self, label_type: LabelTypes, path: str, fname: str = "labels"
    ) -> dict:
        if self.label_subfigs:
            fname = "subfig_" + fname

        with open(f"{self.dir}/{path}/{fname}.json", "r") as f:
            data = json.load(f)

        if label_type == "human":
            return data.get("human", {})

        else:
            human_labels = data.get("human", [])
            matched_labels = {}

            for human_label in human_labels:
                figure_number = human_label.get("figure")
                for label in data.get(label_type, []):
                    if label.get("figure") == figure_number:
                        matched_labels[figure_number] = label
                        break

            return matched_labels

    def intro_modal(self) -> None:
        self.window = tk.Toplevel(self)
        self.window.geometry("400x200")

        self.folder_btn = tk.Button(
            self.window, text="Pick data folder!", command=self._set_folder
        )
        self.folder_btn.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=PADY, padx=PADX
        )

        self.start_text = ttk.Label(self.window, text="Starting paper index:")
        self.start_idx = ttk.Spinbox(self.window, from_=0, to=10000, increment=1)
        self.start_idx.set(0)
        self.start_text.grid(row=1, column=0, pady=PADY)
        self.start_idx.grid(row=1, column=1)

        self.n_papers_text = ttk.Label(
            self.window, text="Number of papers to annotate:"
        )
        self.n_papers = ttk.Spinbox(self.window, from_=0, to=10000, increment=1)
        self.n_papers.set(500)
        self.n_papers_text.grid(row=2, column=0, pady=PADY)
        self.n_papers.grid(row=2, column=1)

        self.window_confirm = tk.Button(
            self.window, text="Confirm", bg="green", command=self._window_confirm
        )
        self.window_confirm.grid(row=3, column=1, pady=(30, 20))

    def pack_widgets(self) -> None:
        self.title_text_var = tk.StringVar(
            self,
            value="Title",
        )
        self.title = tk.Label(
            self,
            textvariable=self.title_text_var,
            font=("", 20),
        )
        self.title.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.img_frame = ttk.LabelFrame(
            self, text="FIGURE", width=int(HALF_W * 0.9), height=int(HALF_W * 0.9)
        )
        self.img_frame.grid_propagate(False)
        self.img = tk.Label(
            self.img_frame, width=int(HALF_W * 0.9), height=int(HALF_W * 0.9)
        )
        self.img.grid(row=0, column=0)
        self.img_frame.grid(
            row=1, column=0, rowspan=4, sticky="nsew", padx=PADX, pady=PADY
        )

        self.caption_frame = ttk.LabelFrame(self, text="CAPTION")
        self.caption_text_var = tk.StringVar(
            self,
            value="Caption",
        )
        self.caption = tk.Label(
            self.caption_frame,
            textvariable=self.caption_text_var,
            wraplength=HALF_W,
            justify="left",
            font=FONT,
        )
        self.caption.grid(row=0, column=0, padx=PADX)
        self.caption_frame.grid(
            row=5, column=0, rowspan=2, sticky="w", padx=PADX, pady=PADY
        )

        self.abstract_frame = ttk.LabelFrame(self, text="ABSTRACT")
        self.abstract_text_var = tk.StringVar(
            self,
            value="Abstract",
        )
        self.abstract = tk.Label(
            self.abstract_frame,
            textvariable=self.abstract_text_var,
            wraplength=HALF_W,
            justify="left",
            font=FONT,
        )
        self.abstract.grid(row=0, column=0, sticky="nsew", padx=PADX)
        self.abstract_frame.grid(row=1, column=1, sticky="w", padx=PADX, pady=PADY)

        self.prop_frame = ttk.LabelFrame(self)

        for i in range(5):
            self.prop_frame.columnconfigure(i, weight=1)
            self.prop_frame.rowconfigure(i, weight=1)

        self.micrograph = InputField(self.prop_frame, "Micrograph: ", "checkbox")
        self.micrograph.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
        )

        self.instrument = InputField(self.prop_frame, "Instrument: ", "dropdown")
        self.instrument.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.material = InputField(self.prop_frame, "Material: ", "entry")
        self.material.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.comments = InputField(self.prop_frame, "Comment: ", "comment")
        self.comments.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.comments.add_btn.config(command=self.add_pressed)
        # TODO: make the add button work!

        self.entries: List[InputField] = [
            self.micrograph,
            self.instrument,
            self.material,
            self.comments,
        ]

        self.switch_text = tk.Label(self.prop_frame, text="Compare:", font=LARGER_FONT)
        self.switch_text.grid(row=5, column=0, sticky="w")
        self.switch_dropdown = ttk.Combobox(
            self.prop_frame,
            values=[
                "none",
                "gpt3_5_with_abstract",
                "gpt3_5_without_abstract",
                "gpt4_with_abstract",
                "gpt4_without_abstract",
                "gpt_4_vision",
                "regex",
            ],
            font=LARGER_FONT,
        )
        self.switch_dropdown.bind("<<ComboboxSelected>>", self._view_select_change)

        self.switch_dropdown.grid(row=5, column=1, sticky="w", padx=(0, 20))
        self.switch_dropdown.current(0)

        self.confirm = tk.Button(
            self.prop_frame,
            text="Confirm",
            font=LARGER_FONT,
            bg="green",
            command=self.confirm_pressed,
        )
        self.confirm.grid(row=5, column=2, sticky="es", padx=(20, 20))

        self.prop_frame.grid(row=2, column=1, sticky="nsew", padx=PADX, pady=PADY)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Micrograph labeller")

    app = App(
        root,
    )

    app.grid()
    root.mainloop()
