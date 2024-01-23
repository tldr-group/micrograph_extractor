import tkinter as tk
from tkinter import ttk


FONT = ("", 14)
LARGER_FONT = ("", 16)
HALF_W = 1000
PADX = (20, 20)
PADY = (10, 10)


class App(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        ttk.Frame.__init__(self)
        self.root = root
        self.root.geometry("800x800")
        # self.root.option_add("*tearOff", False)
        self.pack_widgets()
        # on boot - select folder and starting idx
        #

    def pack_widgets(self) -> None:
        self.title = tk.Label(
            self,
            text="Systems Microbiology and Engineering of Aerobic-Anaerobic Ammonium Oxidation",
            font=("", 20),
        )
        self.title.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.img_frame = ttk.LabelFrame(self, text="FIGURE")  #
        # self.rowconfigure(1, weight=1, minsize=500)
        # self.columnconfigure(0, weight=1, minsize=500)
        self.img_frame.grid(
            row=1, column=0, rowspan=4, sticky="nsew", padx=PADX, pady=PADY
        )

        self.caption_frame = ttk.LabelFrame(self, text="CAPTION")
        self.caption = tk.Label(
            self.caption_frame,
            text="Figure 3. Comparison of bacterial community compositions of bioaggregates sampled from sidestream and mainstream PN/A processes operated at the Eawag experimental hall (Dübendorf, Switzerland) as sequencing batch reactors with high N-loaded anaerobic digester supernatant and with low N-loaded pre-treated municipal wastewater (i.e. organic matter removed beforehand), respectively. In both sidestream and mainstream systems, the AMO genus “Ca. Brocadia” was mainly detected in the biofilms, whereas the AOO genus Nitrosomonas displayed higher relative abundances in the flocs. The NOO genus Nitrospira was mainly detected in flocs at mainstream. The DHO genus Denitratisoma was present in both types of aggregates at sidestream and mainstream. A diversity of heterotrophic organisms and candidate taxa was accompanying the traditional PN/A populations. Saprospiraceae affiliates were abundant, notably in the flocs, and are known to hydrolyse complex carbonaceous substrates. In term of diversity, ca. 30 and 110 operational taxonomic units (OTUs) formed the 75% of the 16S rRNA gene-based amplicon sequencing datasets generated with adaptation to the MiDAS field guide 94 targeting the v4 hypervariable region (Table 1: primer pair 515F / 806R). Taxonomic cutoffs: kingdom (k) > phylum (p) > class (c) > order (o) > family (f) > genus (g) > species (s).",
            wraplength=HALF_W,
            justify="left",
            font=FONT,
        )
        self.caption.grid(row=0, column=0, padx=PADX)
        self.caption_frame.grid(
            row=5, column=0, rowspan=2, sticky="w", padx=PADX, pady=PADY
        )

        self.abstract_frame = ttk.LabelFrame(self, text="ABSTRACT")
        self.abstract = tk.Label(
            self.abstract_frame,
            text="Covalent organic frameworks (COFs) are crystalline, nanoporous materials of interest for various applications. However, current COF synthetic routes lead to insoluble aggregates which hamper processing and prohibit their use in many applications. Here, we report a novel COF synthesis method that produces a stable, homogeneous suspension of crystalline COF nanoparticles. Our approach involves the use of a polar solvent, di-acid catalyst, and slow reagent mixing procedure at elevated temperatures which all together enable access to crystalline COF nanoparticle suspension that does not aggregate or precipitate when kept at elevated temperatures. On cooling, the suspension undergoes a thermoreversible gelation transition to produce crystalline and highly porous COF materials. We demonstrate that this method enables the preparation of COF monoliths, membranes, and films using conventional solution processing techniques. We show that the modified synthesis approach is compatible with various COF chemistries, including both large- and small-pore imine COFs, hydrazone-linked COFs, and COFs with rhombic and hexagonal topology, and in each case, we demonstrate that the final product has excellent crystallinity and porosity. The final materials contain both micro- and macropores, and the total porosity can be tuned through variation of sample annealing. Dynamic light scattering measurements reveal the presence of COF nanoparticles that grow with time at room temperature, transitioning from a homogeneous suspension to a gel. Finally, we prepare imine COF membranes and measure their rejection of polyethylene glycol (PEG) polymers and oligomers, and these measurements exhibit size-dependent rejection of PEG solutes. This work demonstrates a versatile processing strategy to create crystalline and porous COF materials using solution processing techniques and will greatly advance the development of COFs for various applications.",
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

        self.prop_frame.grid(row=2, column=1, sticky="nsew", padx=PADX, pady=PADY)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Micrograph labeller")

    app = App(
        root,
    )

    app.grid()
    root.mainloop()
