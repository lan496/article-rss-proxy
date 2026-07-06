from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import re

from bs4 import BeautifulSoup
import requests

from src.paper import Paper


# chemrxiv.org serves a Cloudflare JS challenge that blocks every plain HTTP
# client (see commit 9784bd5), so fetch preprint metadata from the Crossref
# REST API instead: ChemRxiv deposits all DOIs under the 10.26434 prefix, and
# Crossref indexes new preprints on the same day they are posted.
CROSSREF_CHEMRXIV_URL = "https://api.crossref.org/prefixes/10.26434/works"

# Contact for the Crossref polite pool (better rate limits and stability)
_CROSSREF_MAILTO = "kshinohara0508@gmail.com"

# ChemRxiv posts ~20-40 preprints/day, so one page is more than enough
_MAX_ROWS = 500

# Crossref DOIs are versioned (e.g. 10.26434/chemrxiv-2024-abcde/v2)
_DOI_VERSION_SUFFIX = re.compile(r"/v\d+$")


def fetch_chemrxiv_papers_for_date(date_jst: datetime) -> list[Paper]:
    window_start = (date_jst - timedelta(hours=24)).astimezone(timezone.utc)
    window_end = (date_jst + timedelta(hours=24)).astimezone(timezone.utc)

    params: dict[str, str | int] = {
        "filter": (
            "type:posted-content"
            f",from-posted-date:{window_start.strftime('%Y-%m-%d')}"
            f",until-posted-date:{window_end.strftime('%Y-%m-%d')}"
        ),
        "rows": _MAX_ROWS,
        "mailto": _CROSSREF_MAILTO,
    }
    try:
        response = requests.get(CROSSREF_CHEMRXIV_URL, params=params, timeout=30)
        response.raise_for_status()
        message: dict = response.json()["message"]
    except (requests.RequestException, KeyError, ValueError) as e:
        logging.error(f"Error fetching ChemRxiv works from Crossref: {e}")
        raise

    total = message.get("total-results", 0)
    if total > _MAX_ROWS:
        logging.warning(
            f"Crossref reports {total} ChemRxiv works in window; only first {_MAX_ROWS} used."
        )

    seen_base_dois: set[str] = set()
    papers: list[Paper] = []
    for item in message.get("items", []):
        parsed_date = _parse_posted_date(item)
        if parsed_date is None:
            logging.warning(f"Skipping ChemRxiv entry with malformed posted date: {item.get('DOI')}")
            continue
        if abs(date_jst - parsed_date) > timedelta(hours=24):
            continue

        doi = str(item.get("DOI", ""))
        titles = item.get("title") or []
        if not doi or not titles:
            continue

        # Dedupe revisions: keep only the first version seen per base DOI
        base_doi = _DOI_VERSION_SUFFIX.sub("", doi)
        if base_doi in seen_base_dois:
            continue
        seen_base_dois.add(base_doi)

        papers.append(
            Paper(
                id=doi,
                title=str(titles[0]).strip(),
                link=f"https://doi.org/{doi}",
                summary=_parse_abstract(item),
                authors=_parse_authors(item),
                category="chemrxiv",
                updated=parsed_date.isoformat(),
            )
        )

    return papers


def _parse_posted_date(item: dict) -> datetime | None:
    """Crossref 'posted' has day granularity; interpret it as midnight UTC."""
    date_parts = (item.get("posted") or {}).get("date-parts") or [[]]
    first = date_parts[0]
    if len(first) != 3:
        return None
    try:
        return datetime(first[0], first[1], first[2], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _parse_abstract(item: dict) -> str:
    """Strip JATS markup (<jats:p>, <jats:sup>, ...) from the Crossref abstract."""
    raw = item.get("abstract") or ""
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text()
    return " ".join(text.split())


def _parse_authors(item: dict) -> list[str]:
    result: list[str] = []
    for author in item.get("author") or []:
        name = f"{author.get('given', '')} {author.get('family', '')}".strip()
        if not name:
            name = str(author.get("name", "")).strip()
        if name:
            result.append(name)
    return result
