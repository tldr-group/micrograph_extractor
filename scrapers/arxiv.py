import requests
import xml.etree.ElementTree as ET
from typing import Tuple, List


def make_api_request(
    query_term: str,
    start: int = 0,
    max_results: int = 100,
    sort_by: str = "lastUpdatedDate",
    sort_order="descending",
) -> str:
    url = f"http://export.arxiv.org/api/query?search_query={query_term}&start={start}&max_results={max_results}&sortBy={sort_by}&sortOrder={sort_order}"
    result = requests.get(url)
    return result.text


def handle_entry(entry_elem) -> Tuple[str, str, str]:
    id, summary, published = "", "", ""
    for child in entry_elem:
        if "id" in child.tag:
            id = child.text
        elif "summary" in child.tag:
            summary = child.text
        elif "published" in child.tag:
            published = child.text
    return id, summary, published


def handle_xml(xml_string: str) -> Tuple[List[str], List[str], List[str]]:
    root = ET.fromstring(xml_string)
    ids: List[str] = []
    summaries: List[str] = []
    dates: List[str] = []
    for child in root:
        if "entry" in child.tag:
            id, summary, date = handle_entry(child)
            ids.append(id)
            summaries.append(summary)
            dates.append(date)
    return ids, summaries, dates


def download_pdf(url: str, save_path: str) -> None:
    id = url.split("/")[-1]
    pdf_url = f"http://export.arxiv.org/pdf/{id}.pdf"
    result = requests.get(pdf_url)
    with open(save_path, "wb+") as f:
        f.write(result.content)
