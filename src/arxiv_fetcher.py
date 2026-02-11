from __future__ import annotations

from datetime import timedelta, timezone
import logging
import re
from typing import TYPE_CHECKING

import feedparser
import requests

from src.config import Config
from src.paper import Paper


if TYPE_CHECKING:
    from datetime import datetime


ARXIV_API_URL = (
    "http://export.arxiv.org/api/query?"
    "search_query=cat:{cat}+AND+submittedDate:[{start}+TO+{end}]"
    "&start=0&max_results=1000"
)


def jst_date_to_arxiv_range(date_jst: datetime) -> tuple[str, str]:
    """
    arXiv updates at JST 10:00. Return start/end strings to fetch papers from
    the previous day 11:00 to today 11:00 (24h window).
    On Tuesday, fetch from Friday 11:00 to cover the weekend.
    """
    date_jst11 = date_jst.replace(hour=11, minute=0, second=0, microsecond=0)
    end_utc = date_jst11.astimezone(timezone.utc)
    days_back = 4 if date_jst.weekday() == 1 else 1
    start_utc = end_utc - timedelta(days=days_back)
    return start_utc.strftime("%Y%m%d%H%M"), end_utc.strftime("%Y%m%d%H%M")


def fetch_papers_for_date(date_jst: datetime) -> list[Paper]:
    start_str, end_str = jst_date_to_arxiv_range(date_jst)
    papers: list[Paper] = []
    categories = Config().categories
    for cat in categories:
        url = ARXIV_API_URL.format(cat=cat, start=start_str, end=end_str)
        try:
            response = requests.get(url, timeout=30)
            feed = feedparser.parse(response.text)
            for entry in feed.entries:
                paper = Paper(
                    id=entry.id.split("/")[-1],
                    title=re.sub(r"\s+", " ", entry.title).strip(),
                    link=entry.link,
                    summary=entry.summary.strip(),
                    authors=[a.name for a in entry.authors],
                    category=cat,
                    updated=entry.updated,
                )
                papers.append(paper)
        except Exception as e:
            logging.error(f"Error fetching papers for category {cat}: {e}")
    seen = set()
    unique_papers = []
    for paper in papers:
        if paper.id not in seen:
            unique_papers.append(paper)
            seen.add(paper.id)
    return unique_papers
