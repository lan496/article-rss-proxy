from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
import feedparser
import requests

from src.config import Config
from src.paper import Paper


if TYPE_CHECKING:
    from datetime import datetime

APS_FEED_URL = "https://feeds.aps.org/rss/recent/{journal}.xml"


def _parse_abstract(entry: feedparser.FeedParserDict) -> str:
    content_list = getattr(entry, "content", None)
    if content_list:
        html = content_list[0].get("value", "")
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text.startswith("Author(s):"):
                continue
            parts.append(text)
        if parts:
            return "\n".join(parts)
    return getattr(entry, "summary", "")


def _parse_authors(entry: feedparser.FeedParserDict) -> list[str]:
    author = getattr(entry, "author", None)
    if author:
        return [a.strip() for a in author.replace(" and ", ", ").split(",") if a.strip()]
    return []


def fetch_aps_papers_for_date(date_jst: datetime) -> list[Paper]:
    config = Config()
    target_date_str = date_jst.strftime("%Y-%m-%d")
    papers: list[Paper] = []

    for journal in config.aps_journals:
        url = APS_FEED_URL.format(journal=journal)
        try:
            response = requests.get(url, timeout=30)
            feed = feedparser.parse(response.text)
        except requests.RequestException as e:
            logging.error(f"Error fetching APS feed for {journal}: {e}")
            continue

        for entry in feed.entries:
            entry_date = str(
                getattr(entry, "prism_publicationdate", None)
                or getattr(entry, "updated", "")
            )
            if not entry_date.startswith(target_date_str):
                continue

            paper_id: str = getattr(entry, "prism_doi", None) or entry.get("link", "")
            paper = Paper(
                id=paper_id,
                title=entry.get("title", "").strip(),
                link=entry.get("link", ""),
                summary=_parse_abstract(entry),
                authors=_parse_authors(entry),
                category=getattr(entry, "prism_section", None) or journal,
                updated=entry_date,
            )
            papers.append(paper)

    seen: set[str] = set()
    unique_papers: list[Paper] = []
    for paper in papers:
        if paper.id not in seen:
            unique_papers.append(paper)
            seen.add(paper.id)
    return unique_papers
