# Micrograph Extractor

Scripts for creating, analyzing and evaluating an LLM-labelled micrograph dataset from materials science preprints.   

## Scraping:

1) Find and store the metadata (title, abstract, authors, DOI, date and download URL) of all papers that match the search query `microscopy' on a given preprint server ([arxiv](https://arxiv.org/), [chemrxiv](https://chemrxiv.org/engage/chemrxiv/public-dashboard)). We chose a random sample of 500 chemRxiv papers as a demonstration.
2) Download each paper to a temporary foldeer, extracting all figure/caption pairs and storing them alongside the metadata. 

## Extracting:

### Paired figure/caption extraction  

[pdffigures2](https://github.com/allenai/pdffigures2): scala program for extracting figures and associated captions from figures.

For single files:
```
sbt "runMain org.allenai.pdffigures2.FigureExtractorVisualizationCli /absolute/file/path/file.pdf"
```

For batch processing a whole directory and then saving files to imgs/ and captions to /data with a DPI of 200:
```
sbt "runMain org.allenai.pdffigures2.FigureExtractorBatchCli /home/ronan/Documents/uni_work/phd/micrograph_extractor/data/ -m /home/ronan/Documents/uni_work/phd/micrograph_extractor/outputs/imgs/ -d /home/ronan/Documents/uni_work/phd/micrograph_extractor/outputs/data/ -i 200"
```

### Subfigure detection

1) Threshold segment whole image into pixels that are white and that are not
2) Perform binary opening to remove small gaps
3) Do connected-component analysis of non-white regions and get bounding boxes per component

NB: this assumes sub-figures are separated with white gutters of ~>2px. This is generally true, but not always - some figures have no whitespace (*i.e,* timeseries), which is relevant when performing VLM analysis later.  


## Analysis

### LLM analysis
GPT3.5/4 was prompted with the figure's caption and abstract and asked to identify whether the associated figure contained a micrograph, and if so what technique (AFM, TEM, SEM, *etc.*) was used to image it and what material was being imaged, as well as any additional comments for, say, processing conditions. The `.json` structure for a figure that contained the micrograph was as follows:

```
{
    "isMicrograph": "true",
    "instrument": "Technique",
    "material": "Description",
    "comments": ["comment1", "comment2", "comment3"]
}
```
We tested giving the LLM both the caption and abstract and just the caption - we found providing both worked the best (in terms of balancing sensitivty and specificity). The good performance is a function of how well-structured scientific paper captions tend to be. **In many ways, this is an easy task that only an LLM can do**. 

### VLM analysis
GPT3.5/4 is effective at detecting *if* a figure contains a micrograph, but it cannot tell you which sub-figure is the micrograph(s). To do this we analyzed each figure that GPT3.5/4 labelled as containing a micrograph and its extracted sub-figures. We fed the figure caption, paper abstract, specific sub-figure and the whole figure to GPT4-V and asked it if the specific sub-figure was a single micrograph (i.e, not a timeseries or unextracted figure). 

Any single micrographs were placed into a the dataset in `micrographs/`, with their labels, DOI, *etc.* in `micrographs/label.csv`.


### Regex
We compared the accuracy of LLM micrograph detection to two string-matching/regex approaches. The 'simple' regex said a micrograph was detected if the caption contained the substring "image" or "micrograph" anywhere. The 'greedy' regex said a micrograph was detected if any instrument name ("SEM" or "Scanning Electron Microscopy" or "TEM" *etc.*) was detected or if it contained "image" or "micrograph" as before.

The 'simple' regex scheme was remarkably effective (if slightly conservative), probably because scientific captions are well-structured. The 'greedy' regex had too many false positives, as could be expected.

### Evaluation
We wrote a custom labelling app (in `labelling_app/`) that allows humans to label the extracted figures and sub-figures and compare the LLM/regex labels to the human labels for evaluation.

## Installation:

1. Create a virtual environment in python:
```
python3.10 -m venv .venv
source venv/bin/activate
```
2. Install python dependencies:
```
pip install -r requirements.txt
```
3. Install pdffigures2 and scala build tool (sbt) using `build.sh` (right-click and tick 'allow running as a program')
```
.\build.sh
```