import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
from tkinter import filedialog as fd
from os import listdir
from json import load, dump

from typing import Literal, Tuple, List

import re

FONT = ("", 14)
LARGER_FONT = ("", 16)
HALF_W = 1000
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


def sort_human(l):
    # user Julian (https://stackoverflow.com/questions/3426108/how-to-sort-a-list-of-strings-numerically)
    convert = lambda text: float(text) if text.isdigit() else text
    alphanum = lambda key: [convert(c) for c in re.split("([-+]?[0-9]*\.?[0-9]*)", key)]
    l.sort(key=alphanum)
    return l


class App(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        ttk.Frame.__init__(self)
        self.root = root
        self.root.geometry("800x800")

        self.pack_widgets()
        self.intro_modal()
        self.dir: str
        self.start: int
        self.n: int
        self.paper_idx: int = 0
        self.figure_idx: int = 0
        self.total_figures: int = 0
        self.paper_paths: List[str] = []
        self.fig_comments: List[str] = []

        self.current_paper_data: List[dict] = []

    def _set_folder(self) -> None:
        self.dir = open_file_dialog_return_fps()

    def _window_confirm(self) -> None:
        self.start = int(self.start_idx.get())
        self.n = int(self.n_papers.get())
        self.window.destroy()
        self.start_logic(self.dir, self.start, self.n)

    def start_logic(self, folder: str, start_idx: int, n_papers: int) -> None:
        all_papers = listdir(folder)
        self.paper_paths = all_papers[start_idx : start_idx + n_papers]
        self.load_paper(self.paper_paths[0])

    def load_paper(self, path: str) -> None:
        print(path)
        metadata_path = f"{self.dir}/{path}/paper_data.json"
        captions_path = f"{self.dir}/{path}/captions.json"
        imgs_path = f"{self.dir}/{path}/imgs"

        self.metadata = load_json(metadata_path)
        self.title_text_var.set(self.metadata["title"])
        self.abstract_text_var.set(self.metadata["abstract"])

        self.captions = self.load_captions(captions_path)
        self.img_paths = sort_human(listdir(imgs_path))
        self.total_figures = len(self.img_paths)
        self.load_img(f"{self.dir}/{path}/imgs/{self.img_paths[0]}")

    def load_captions(self, captions_path: str) -> List[str]:
        # assumes no missing figures - wrong assumption
        captions_dict: List[dict] = load_json(captions_path)

        valid_figures: List[dict] = filter(
            lambda x: x["figType"] == "Figure", captions_dict
        )
        figure_dict = sorted(valid_figures, key=lambda x: int(x["name"]))
        captions = list(map(lambda x: x["caption"], figure_dict))

        # TODO: make this mapping a dict of figure name to caption so not indexing a list later

        """
        stop = False
        i = 0
        captions = []
        while stop == False:
            result = get_caption(captions_dict, i + 1)
            if result == "not found":
                stop = True
            else:
                captions.append(result)
                i += 1
        """

        self.caption_text_var.set(captions[0])
        return captions

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
        # self.img.grid(row=0, column=0, sticky="nsew")

    def add_pressed(self) -> None:
        comment: str = str(self.comments.get())
        self.fig_comments.append(comment)
        self.comments.delete(0, tk.END)

    def confirm_pressed(self) -> None:
        fig, subfig = get_fig_and_subfig_n(self.img_paths[self.figure_idx])
        is_micrograph = self.micrograph_var.get()

        data: dict
        if not is_micrograph:
            data = {"figure": fig, "subfigure": subfig, "isMicrograph": is_micrograph}
        else:
            data = {
                "figure": fig,
                "subfigure": subfig,
                "isMicrograph": is_micrograph,
                "instrument": self.instrument.get(),
                "material": self.material.get(),
                "comments": self.fig_comments,
            }
        self.current_paper_data.append(data)
        self.fig_comments = []
        self.figure_idx += 1
        print(f"Figure [{self.figure_idx} / {self.total_figures}]")

        if self.figure_idx >= self.total_figures:
            path = self.paper_paths[self.paper_idx]
            save_json(f"{self.dir}/{path}/human_label.json", self.current_paper_data)
            self.paper_idx += 1
            print(f"Paper [{self.paper_idx} / {self.n}]")
            self.figure_idx = 0
            new_path = self.paper_paths[self.paper_idx]
            self.current_paper_data = []
            self.load_paper(new_path)
        else:
            new_fig_n, new_subfig_n = get_fig_and_subfig_n(
                self.img_paths[self.figure_idx]
            )
            print(new_fig_n, new_subfig_n)
            self.caption_text_var.set(self.captions[new_fig_n - 1])
            self.load_img(self.get_full_img_path(self.figure_idx))

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
            value="Systems Microbiology and Engineering of Aerobic-Anaerobic Ammonium Oxidation",
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
        self.img.grid_propagate(False)
        self.img.grid(row=0, column=0)
        self.img_frame.grid(
            row=1, column=0, rowspan=4, sticky="nsew", padx=PADX, pady=PADY
        )

        self.caption_frame = ttk.LabelFrame(self, text="CAPTION")
        self.caption_text_var = tk.StringVar(
            self,
            value="Figure 3. Comparison of bacterial community compositions of bioaggregates sampled from sidestream and mainstream PN/A processes operated at the Eawag experimental hall (Dübendorf, Switzerland) as sequencing batch reactors with high N-loaded anaerobic digester supernatant and with low N-loaded pre-treated municipal wastewater (i.e. organic matter removed beforehand), respectively. In both sidestream and mainstream systems, the AMO genus “Ca. Brocadia” was mainly detected in the biofilms, whereas the AOO genus Nitrosomonas displayed higher relative abundances in the flocs. The NOO genus Nitrospira was mainly detected in flocs at mainstream. The DHO genus Denitratisoma was present in both types of aggregates at sidestream and mainstream. A diversity of heterotrophic organisms and candidate taxa was accompanying the traditional PN/A populations. Saprospiraceae affiliates were abundant, notably in the flocs, and are known to hydrolyse complex carbonaceous substrates. In term of diversity, ca. 30 and 110 operational taxonomic units (OTUs) formed the 75% of the 16S rRNA gene-based amplicon sequencing datasets generated with adaptation to the MiDAS field guide 94 targeting the v4 hypervariable region (Table 1: primer pair 515F / 806R). Taxonomic cutoffs: kingdom (k) > phylum (p) > class (c) > order (o) > family (f) > genus (g) > species (s).",
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
            value="Covalent organic frameworks (COFs) are crystalline, nanoporous materials of interest for various applications. However, current COF synthetic routes lead to insoluble aggregates which hamper processing and prohibit their use in many applications. Here, we report a novel COF synthesis method that produces a stable, homogeneous suspension of crystalline COF nanoparticles. Our approach involves the use of a polar solvent, di-acid catalyst, and slow reagent mixing procedure at elevated temperatures which all together enable access to crystalline COF nanoparticle suspension that does not aggregate or precipitate when kept at elevated temperatures. On cooling, the suspension undergoes a thermoreversible gelation transition to produce crystalline and highly porous COF materials. We demonstrate that this method enables the preparation of COF monoliths, membranes, and films using conventional solution processing techniques. We show that the modified synthesis approach is compatible with various COF chemistries, including both large- and small-pore imine COFs, hydrazone-linked COFs, and COFs with rhombic and hexagonal topology, and in each case, we demonstrate that the final product has excellent crystallinity and porosity. The final materials contain both micro- and macropores, and the total porosity can be tuned through variation of sample annealing. Dynamic light scattering measurements reveal the presence of COF nanoparticles that grow with time at room temperature, transitioning from a homogeneous suspension to a gel. Finally, we prepare imine COF membranes and measure their rejection of polyethylene glycol (PEG) polymers and oligomers, and these measurements exhibit size-dependent rejection of PEG solutes. This work demonstrates a versatile processing strategy to create crystalline and porous COF materials using solution processing techniques and will greatly advance the development of COFs for various applications.",
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

        self.micrograph_text = tk.Label(
            self.prop_frame, text="Micrograph:", font=LARGER_FONT
        )
        self.micrograph_var = tk.BooleanVar(self, value=False)
        self.micrograph = tk.Checkbutton(
            self.prop_frame, text="Yes", font=LARGER_FONT, variable=self.micrograph_var
        )
        self.micrograph_text.grid(row=1, column=0, sticky="w", padx=PADX, pady=PADY)
        self.micrograph.grid(row=1, column=1, sticky="ew")

        self.instrument_text = tk.Label(
            self.prop_frame, text="Instrument:", font=LARGER_FONT
        )
        self.instrument = ttk.Combobox(
            self.prop_frame,
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
        )
        self.instrument.current(0)

        self.instrument_text.grid(row=2, column=0, sticky="w", padx=PADX, pady=PADY)
        self.instrument.grid(row=2, column=1, sticky="ew")

        self.material_text = tk.Label(
            self.prop_frame, text="Material:", font=LARGER_FONT
        )
        self.material = tk.Entry(self.prop_frame, font=LARGER_FONT)

        self.material_text.grid(row=3, column=0, sticky="w", padx=PADX, pady=PADY)
        self.material.grid(row=3, column=1, sticky="ew")

        self.comments_text = tk.Label(
            self.prop_frame, text="Comments:", font=LARGER_FONT
        )
        self.comments = tk.Entry(self.prop_frame, font=LARGER_FONT)
        self.comments_add = tk.Button(
            self.prop_frame, text="Add", font=LARGER_FONT, command=self.add_pressed
        )

        self.comments_text.grid(row=4, column=0, sticky="w", padx=PADX, pady=PADY)
        self.comments.grid(row=4, column=1, sticky="ew")
        self.comments_add.grid(row=4, column=2)

        self.confirm = tk.Button(
            self.prop_frame,
            text="Confirm",
            font=LARGER_FONT,
            bg="green",
            command=self.confirm_pressed,
        )
        self.confirm.grid(row=5, column=2, sticky="es", padx=(20, 20), pady=(80, 10))

        self.prop_frame.grid(row=2, column=1, sticky="nsew", padx=PADX, pady=PADY)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Micrograph labeller")

    app = App(
        root,
    )

    app.grid()
    root.mainloop()
