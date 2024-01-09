# Micrograph Extractor

Find, extract and describe all micrographs in a paper's `.pdf` using (V)LLMs. When applied to a large corpus of open-access papers, this should produce a large, varied library of micrographs with weak labels detailing the imaging technique, material studied and other useful information.

This will involve 3 steps:
1) Collection of a large amount of open-access papers that are likely to include micrographs from preprint servers like [arxiv](https://arxiv.org/), [chemrxiv](https://chemrxiv.org/engage/chemrxiv/public-dashboard) and [biorxiv](https://www.biorxiv.org/). arxiv has an [API for metadata](https://info.arxiv.org/help/api/index.html) for bulk download based on queries, limited at a rate of 1 request per 3 seconds. It might be easier to only download articles that fulfil a search query, by pinging `export.arxiv.org`, which is limited to 4 requests per second with a 1 second sleep after. 
2) Extracting all figures and captions from a given `.pdf`, via a `.pdf` scraper like [pypdf](https://pypi.org/project/pypdf/), [PDFigCapX](https://github.com/pengyuanli/PDFigCapX) or [pdffigures2](https://github.com/allenai/pdffigures2). Composite figures (ones with a (a), (b), (c), ...) will need to be decomposed if being saved later, potentially by looking for whitespace between sub-figures.
3) Querying a (V)LLM with the image + figure caption, asking it a few questions about the figure, namely if it has a micrograph(s), what instrument was used, which material was used, does it have a scale-bar *etc*. 

## Questions:

- How often does the (V)LLM correctly identify a micrograph?
- How often does the (V)LLM correctly identify the imaging technique?
- How often does the (V)LLM correctly identify the material?
- How often does the (V)LLM correctly identify a scale-bar?
- How does the performance change with different models? How does the performance compare to a simple regex?
- Where does it go wrong, and why?
- How does performance change when the level of information in the prompt changes (*i.e,* explaining different imaging techniques, telling it it's a materials scientist, explaining what a micrograph is)
- Is a VLM needed or does the LLM work well enough on the caption alone? 

## Models:

### Extracting:
- [paperscraper](https://github.com/PhosphorylatedRabbits/paperscraper): python library for scraping metadata and/or pdfs from arxiv, chemrxiv *etc*. It can scrape based on a keyword query.
- [pdffigures2](https://github.com/allenai/pdffigures2): scala program for extracting figures and associated captions from figures. Only tested on computer science papers so will see how well it translates to pre-prints.

For single files:
```
sbt "runMain org.allenai.pdffigures2.FigureExtractorVisualizationCli /absolute/file/path/file.pdf"
```

For batch processing a whole directory and then saving files to imgs/ and captions to /data with a DPI of 200:
```
sbt "runMain org.allenai.pdffigures2.FigureExtractorBatchCli /home/ronan/Documents/uni_work/phd/micrograph_extractor/data/ -m /home/ronan/Documents/uni_work/phd/micrograph_extractor/data/out/imgs/ -d /home/ronan/Documents/uni_work/phd/micrograph_extractor/data/out/data/ -i 200"
```

### LLMS:
- [GPT-4](https://openai.com/blog/openai-api): captions only, will cost money (but not much?).
- [llama](https://github.com/facebookresearch/llama): can be deployed locally.
- [llama.cpp](https://github.com/ggerganov/llama.cpp): can run on lower-end devices.


### VLMS:
- [TinyGPT-V](https://github.com/DLYuanGod/TinyGPT-V): distilled VLM designed to run on low-end graphics cards (8GB RAM).
- [GPT-4v](https://openai.com/blog/openai-api): captions + figure analysis, will cost money.
- [llava](https://llava-vl.github.io/): 4 bit quantization -> could run on 12GB VRAM like ours.