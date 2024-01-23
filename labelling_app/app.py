import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from os import listdir

from typing import Literal, Tuple, List

FONT = ("", 14)
LARGER_FONT = ("", 16)
HALF_W = 1000
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

    def _set_folder(self) -> None:
        self.dir = open_file_dialog_return_fps()

    def _window_confirm(self) -> None:
        self.start = int(self.start_idx.get())
        self.n = int(self.n_papers.get())
        self.window.destroy()
        self.start_logic(self.dir, self.start, self.n)

    def start_logic(self, folder: str, start_idx: int, n_papers: int) -> None:
        all_papers = listdir(folder)
        self.paper_paths: List[str] = all_papers[start_idx : start_idx + n_papers]
        print(self.paper_paths)

    def load_paper(self, path: str) -> None:
        pass

    def pack_widgets(self) -> None:
        self.title = tk.Label(
            self,
            text="Systems Microbiology and Engineering of Aerobic-Anaerobic Ammonium Oxidation",
            font=("", 20),
        )
        self.title.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.img_frame = ttk.LabelFrame(self, text="FIGURE")  #
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
        self.micrograph = tk.Checkbutton(self.prop_frame, text="Yes", font=LARGER_FONT)
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
                "Other",
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
        self.comments_add = tk.Button(self.prop_frame, text="Add", font=LARGER_FONT)

        self.comments_text.grid(row=4, column=0, sticky="w", padx=PADX, pady=PADY)
        self.comments.grid(row=4, column=1, sticky="ew")
        self.comments_add.grid(row=4, column=2)

        self.confirm = tk.Button(
            self.prop_frame, text="Confirm", font=LARGER_FONT, bg="green"
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
