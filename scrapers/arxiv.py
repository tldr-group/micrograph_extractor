import requests
import xml.etree.ElementTree as ET
from typing import Tuple, List

from .generic import GenericScraper, PaperEntry, make_folder, asdict, dump


class ArxivScraper(GenericScraper):
    def scrape(
        self,
        query: str,
        start: int = 0,
        max_results: int = 50,
        sort_by: str = "lastUpdatedDate",
        sort_order="descending",
    ) -> int:
        result = self.make_api_request(query, start, max_results, sort_by, sort_order)
        n_papers = self.handle_entries(result)  # type: ignore
        return n_papers

    def make_api_request(
        self,
        query_term: str,
        start: int = 0,
        max_results: int = 100,
        sort_by: str = "lastUpdatedDate",
        sort_order="descending",
    ) -> str:
        url = f"http://export.arxiv.org/api/query?search_query={query_term}&start={start}&max_results={max_results}&sortBy={sort_by}&sortOrder={sort_order}"
        result = requests.get(url)
        return result.text

    def handle_entries(  # type: ignore[override]
        self, entries: str, dataset_path: str = "dataset/papers/"
    ) -> int:
        n_papers = 0
        root = ET.fromstring(entries)
        for child in root:
            if "entry" in child.tag:
                paper_entry = self.handle_entry(child)
                folder_name = self.doi_to_folder_name(paper_entry.doi)
                make_folder(dataset_path + folder_name)
                self.save_paper_data(paper_entry, dataset_path + folder_name)
                n_papers += 1
        return n_papers

    def handle_entry(self, entry_elem: ET.Element) -> PaperEntry:  # type: ignore[override]
        id, title, authors, abstract, date = "", "", [], "", ""
        for child in entry_elem:
            if "id" in child.tag:
                id = child.text
            elif "summary" in child.tag:
                abstract = child.text
            elif "published" in child.tag:
                date = child.text
            elif "author" in child.tag:
                authors.append(child[0].text)
        doi = self.url_to_doi(id)
        values = [id, doi, title, authors, abstract, date]
        return PaperEntry(*values)  # type: ignore

    def url_to_doi(self, url: str) -> str:
        end = url.split("/")[-1]
        return "arXiv:" + end

    def doi_to_folder_name(self, doi: str):
        return doi.replace(":", "_").lower()

    def save_paper_data(self, paper_entry: PaperEntry, path: str) -> None:
        paper_dict = asdict(paper_entry)
        with open(path + "/paper_data.json", "w+") as f:
            dump(paper_dict, f, ensure_ascii=False, indent=4)

    def download_pdf(self, paper_id: str, save_path: str) -> None:
        id = paper_id.split("/")[-1]
        pdf_url = f"http://export.arxiv.org/pdf/{id}.pdf"
        result = requests.get(pdf_url)
        with open(save_path, "wb+") as f:
            f.write(result.content)
