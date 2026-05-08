from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from bs4 import BeautifulSoup
import feedparser
import requests

from src.config import Config
from src.paper import Paper


CHEMRXIV_FEED_URL = (
    "https://chemrxiv.org/action/showFeed"
    "?type=search&format=rss&query=ConceptID%3D{concept_id}"
)
# Cloudflare blocks the default python-requests user agent.
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh, Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _parse_summary(entry: feedparser.FeedParserDict) -> str:
    content_list = getattr(entry, "content", None)
    if content_list:
        html = content_list[0].get("value", "")
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(strip=True)
    return getattr(entry, "summary", "")


def _parse_authors(entry: feedparser.FeedParserDict) -> list[str]:
    authors_list = getattr(entry, "authors", None)
    if authors_list:
        return [a.get("name", "").strip() for a in authors_list if a.get("name", "").strip()]
    return []


def fetch_chemrxiv_papers_for_date(date_jst: datetime) -> dict[str, list[Paper]]:
    config = Config()
    papers_by_concept: dict[str, list[Paper]] = {}

    session = requests.Session()
    session.headers.update({"User-Agent": _BROWSER_UA})

    for concept, concept_id in config.chemrxiv_concepts.items():
        url = CHEMRXIV_FEED_URL.format(concept_id=concept_id)
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
        except requests.RequestException as e:
            logging.error(f"Error fetching ChemRxiv feed for {concept}: {e}")
            continue

        seen: set[str] = set()
        concept_papers: list[Paper] = []
        for entry in feed.entries:
            entry_date = str(getattr(entry, "dc_date", "") or getattr(entry, "updated", ""))
            try:
                parsed_date = datetime.fromisoformat(entry_date.replace("Z", "+00:00"))
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                logging.warning(f"Skipping entry with malformed date: {entry_date}")
                continue
            if abs(date_jst - parsed_date) > timedelta(hours=24):
                continue

            paper_id: str = getattr(entry, "prism_doi", None) or entry.get("link", "")
            if paper_id in seen:
                continue
            seen.add(paper_id)

            concept_papers.append(
                Paper(
                    id=paper_id,
                    title=entry.get("title", "").strip(),
                    link=entry.get("link", ""),
                    summary=_parse_summary(entry),
                    authors=_parse_authors(entry),
                    category=concept,
                    updated=parsed_date.isoformat(),
                )
            )

        if concept_papers:
            papers_by_concept[concept] = concept_papers

    return papers_by_concept
