from typing import List, Tuple
import xml.etree.ElementTree as ET
from os import mkdir
from dataclasses import dataclass, asdict
from json import dump


@dataclass
class PaperEntry:
    url: str
    doi: str
    title: str
    authors: List[str]
    abstract: str
    date: str


def make_folder(dir_name: str) -> None:
    try:
        mkdir(dir_name)
    except FileExistsError:
        pass


class GenericScraper:
    def make_api_request(
        self,
        query_term: str,
        start: int = 0,
        max_results: int = 100,
        sort_by: str = "lastUpdatedDate",
        sort_order="descending",
    ) -> str | dict:
        return "null"

    def get_authors(self, author_list) -> List[str]:
        return []

    def handle_entry(self, entry: dict | ET.Element) -> PaperEntry:
        return PaperEntry(
            "null",
            "null",
            "null",
            ["null"],
            "null",
            "null",
        )

    def handle_entries(self, entries: str | dict) -> None:
        return

    def download_pdf(self, paper_id: str, save_path: str) -> None:
        return
