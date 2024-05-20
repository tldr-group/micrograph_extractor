from os import getcwd, makedirs
from os.path import join
from extract import single_pdf_extract_process, CWD
from analyze import single_regex_label

llm_available = False
try:
    from llm_operations.run_llm_with_abstract import assistant
    from llm_operations.gpt_utils import extract_json_from_response

    llm_available = True
except:
    pass
from labelling_app.app import load_json

import unittest


extract_fail_message = """
No captions/figures extracted from the PDF!
Potential causes:
- missing input pdf in test_data
- FigureExtractor not built properly - make sure user permissions on pdffigures2/ set right and `sbt build` 
has been successfully run in the `pdffigures2` directory
- some bug in the folder structure/os mkdirs
"""

llm_fail_message = """
No captions analyzed by GPT!
Potential causes:
- no OPENAI_API_KEY env variable set
- no internet connection
- timeout on the API request

"""

abstract = """The mesostructure of porous electrodes used in lithium-ion batteries strongly inﬂuences cell performance. Accurate imaging of the
distribution of phases in these electrodes would allow this relationship to be better understood through simulation. However,
imaging the nanoscale features in these components is challenging. While scanning electron microscopy is able to achieve the
required resolution, it has well established difﬁculties imaging porous media. This is because the ﬂat imaging planes prepared using
focused ion beam milling will intersect with the pores, which makes the images hard to interpret as the inside walls of the pores are
observed. It is common to inﬁltrate porous media with resin prior to imaging to help resolve this issue, but both the nanoscale
porosity and the chemical similarity of the resins to the battery materials undermine the utility of this approach for most electrodes.
In this study, a technique is demonstrated which uses in situ inﬁltration of platinum to ﬁll the pores and thus enhance their contrast
during imaging. Reminiscent of the Japanese art of repairing cracked ceramics with precious metals, this technique is referred to as
the kintsugi method. The images resulting from applying this technique to a conventional porous cathode are presented and then
segmented using a multi-channel convolutional method. We show that while some cracks in active material particles were empty,
others appear to be ﬁlled (perhaps with the carbon binder phase), which will have implications for the rate performance of the cell.
Energy dispersive X-ray spectroscopy was used to validate the distribution of phases resulting from image analysis, which also
suggested a graded distribution of the binder relative to the carbon additive. The equipment required to use the kintsugi method is
commonly available in major research facilities and so we hope that this method will be rapidly adopted to improve the imaging of
electrode materials and porous media in general."""


class Tests(unittest.TestCase):
    # add scraping test?

    def test_extraction(self):
        """Run figure/caption extractor on the test pdf `test_data/tmp.pdf`, splitting extracted figures
        into subfigures as well. Outputs original and sub-figures to `test_data/processed/` folder. Fails
        if no figures extracted."""
        target_dir = join(CWD, "test_data/")
        target_pdf = join(target_dir, "tmp.pdf")

        out_img_dir = join(CWD, "test_data/out/imgs/")
        out_data_dir = join(CWD, "test_data/out/")

        processed_dir = join(CWD, "test_data/processed/")

        for new_dir in [target_dir, out_img_dir, processed_dir]:
            makedirs(new_dir, exist_ok=True)

        captions, _ = single_pdf_extract_process(
            target_pdf, out_img_dir, out_data_dir, processed_dir
        )
        assert len(captions) > 0, extract_fail_message

    def test_regex(self):
        """Run basic string matching caption/instrument analysis on the captions of the pdf."""
        labels_path = join(CWD, "test_data/analyze/labels.json")
        captions_path = join(CWD, "test_data/analyze/captions.json")
        out = single_regex_label(labels_path, captions_path)
        li = out["regex"]
        assert (
            len(li) > 0
        ), "Failed to analyze captions with regex - files may be in the wrong place."
        for figure_eval in li:
            assert figure_eval["isMicrograph"] == True, "Incorrect regex eval"

    def test_gpt(self):
        """Run LLM-based caption analysis on the captions. Requires the OPENAI_API_KEY environment
        variable to be set."""
        if llm_available is False:
            assert (
                llm_available
            ), "Need to set OPENAI_API_KEY environment variable before LLM labelling"
        labels_path = join(CWD, "test_data/analyze/labels.json")
        captions_path = join(CWD, "test_data/analyze/captions.json")

        labels_data = load_json(labels_path)
        captions_data = load_json(captions_path)

        llm_labels = []
        for item in captions_data:
            caption = item["caption"]
            figure_type = item["figType"]
            if figure_type == "Figure":
                response = assistant(abstract, caption)
                response_data = extract_json_from_response(response)
                response_data["figure"] = captions_data["name"]
                llm_labels.append(response_data)
        labels_data["llm"] = llm_labels
        assert len(llm_labels) > 0, llm_fail_message


if __name__ == "__main__":
    unittest.main()
