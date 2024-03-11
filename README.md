# Micrograph Extractor

Scripts for creating, analyzing and evaluating an LLM-labelled micrograph dataset from materials science preprints.   


Method:
1) Collects a large amount of open-access papers that are likely to include micrographs from preprint servers like  and [biorxiv](https://www.biorxiv.org/). arxiv has an [API for metadata](https://info.arxiv.org/help/api/index.html) for bulk download based on queries, limited at a rate of 1 request per 3 seconds. `export.arxiv.org` is the API-portal and is limited to 4 requests per second with a 1 second sleep after. 
2) Extracts all figures and captions from a given `.pdf`, via the [pdffigures2](https://github.com/allenai/pdffigures2) `.pdf` scraper. Composite figures (ones with a (a), (b), (c), ...) are decomposed by looking for whitespace between sub-figures, thresholding and detecting connected-components.
3) A (V)LLM is queried with the figure caption and/or image, asking it a few questions about the figure, namely if it has a micrograph(s), what instrument was used, which material was imaged and whether it have a scale-bar *etc*.
4) A custom gui in `labelling_app/`allows human labelling of scraped image/caption pairs and later comparison with LLM labels

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


### Regex


### Evaluation


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