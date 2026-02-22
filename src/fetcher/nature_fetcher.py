from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from bs4 import BeautifulSoup
import feedparser
import requests

from src.config import Config
from src.paper import Paper


NATURE_FEED_URL = "https://www.nature.com/{journal}.rss"


def _parse_summary(entry: feedparser.FeedParserDict) -> str:
    content_list = getattr(entry, "content", None)
    if content_list:
        html = content_list[0].get("value", "")
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(strip=True)
    return getattr(entry, "summary", "")


def _parse_authors(entry: feedparser.FeedParserDict) -> list[str]:
    # feedparser collects multiple dc:creator elements into entry.authors
    authors_list = getattr(entry, "authors", None)
    if authors_list:
        return [a.get("name", "").strip() for a in authors_list if a.get("name", "").strip()]
    return []


def fetch_nature_papers_for_date(date_jst: datetime) -> dict[str, list[Paper]]:
    config = Config()
    papers_by_journal: dict[str, list[Paper]] = {}

    for journal in config.nature_journals:
        url = NATURE_FEED_URL.format(journal=journal)
        try:
            response = requests.get(url, timeout=30)
            feed = feedparser.parse(response.text)
        except requests.RequestException as e:
            logging.error(f"Error fetching Nature feed for {journal}: {e}")
            continue

        seen: set[str] = set()
        journal_papers: list[Paper] = []
        for entry in feed.entries:
            entry_date = str(getattr(entry, "dc_date", "") or getattr(entry, "updated", ""))
            try:
                parsed_date = datetime.fromisoformat(entry_date)
                # Nature dc:date is naive (e.g. "2026-02-21"); assume UTC
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

            paper = Paper(
                id=paper_id,
                title=entry.get("title", "").strip(),
                link=entry.get("link", ""),
                summary=_parse_summary(entry),
                authors=_parse_authors(entry),
                category=journal,
                updated=parsed_date.isoformat(),
            )
            journal_papers.append(paper)

        if journal_papers:
            papers_by_journal[journal] = journal_papers

    return papers_by_journal
