import requests
from typing import Tuple, List
from json import dump, loads

from .generic import PaperEntry, GenericScraper, make_folder, asdict


class ChemrxivScraper(GenericScraper):
    def scrape(
        self,
        query: str,
        start: int = 0,
        max_results: int = 50,
        sort_by: str = "lastUpdatedDate",
        sort_order="PUBLISHED_DATE_DESC",
    ) -> int:
        result = self.make_api_request(query, start, max_results, sort_by, sort_order)
        n_papers = result["totalCount"]
        if n_papers == 0:
            print("WARNING: no results!")
            print(result)
        self.handle_entries(result)  # type: ignore
        return n_papers

    def make_api_request(
        self,
        query_term: str,
        start: int = 0,
        max_results: int = 100,
        sort_by: str = "lastUpdatedDate",
        sort_order="PUBLISHED_DATE_DESC",
    ) -> str | dict:
        url = f'https://chemrxiv.org/engage/chemrxiv/public-api/v1/items?term="{query_term}"&skip={start}&limit={max_results}&sort={sort_order}'
        result = requests.get(url)
        return result.json()

    def handle_entries(self, entries: dict, dataset_path: str = "dataset/papers/") -> None:  # type: ignore[override]
        item_list = entries["itemHits"]
        for _item in item_list:
            item = _item["item"]
            paper_entry = self.handle_entry(item)
            folder_name = self.doi_to_folder_name(paper_entry.doi)
            make_folder(dataset_path + folder_name)
            self.save_paper_data(paper_entry, dataset_path + folder_name)
            # save paper data to a .json in that folder

    def handle_entry(self, json_entry: dict) -> PaperEntry:  # type: ignore[override]
        values = []
        for key in ["id", "doi", "title", "authors", "abstract", "submittedDate"]:
            value: str | List[str]
            try:
                entry = json_entry[key]
                value = self.get_value(key, entry)
            except KeyError:
                value = "null" if key != "authors" else ["null"]
            values.append(value)
        return PaperEntry(*values)  # type: ignore

    def get_authors(self, author_list: List[dict]) -> List[str]:
        authors = []
        for item in author_list:
            author = item["firstName"] + " " + item["lastName"]
            authors.append(author)
        return authors

    def get_value(self, key: str, json_entry: dict) -> str | List[str]:
        if key != "authors":
            return json_entry
        else:
            return self.get_authors(json_entry)

    def doi_to_folder_name(self, doi: str) -> str:
        stripped = (
            doi.replace(".", "_")
            .replace("/", "")
            .replace("-", "_")
            .replace("chemrxiv", "")
        )
        added = "chemrxiv_" + stripped
        return added

    def save_paper_data(self, paper_entry: PaperEntry, path: str) -> None:
        paper_dict = asdict(paper_entry)
        with open(path + "/paper_data.json", "w+") as f:
            dump(paper_dict, f, ensure_ascii=False, indent=4)

    def download_pdf(self, paper_id: str, save_path: str) -> None:
        pdf_url = f"https://chemrxiv.org/engage/api-gateway/chemrxiv/assets/orp/resource/item/{paper_id}/original/paper.pdf"
        result = requests.get(pdf_url)
        with open(save_path, "wb+") as f:
            f.write(result.content)
