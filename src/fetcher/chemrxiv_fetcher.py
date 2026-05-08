from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

import requests

from src.config import Config
from src.paper import Paper


_CATEGORIES_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/categories"
_DISCIPLINES_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/disciplines"
_ITEMS_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items"

_WARMUP_URL = "https://chemrxiv.org/engage/chemrxiv/search-dashboard"

# Full browser headers to satisfy Cloudflare bot-mitigation checks.
# The warmup GET to _WARMUP_URL seeds the __cf_bm cookie before API calls.
_BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://chemrxiv.org",
    "Referer": _WARMUP_URL,
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not?A_Brand";v="8"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}


def _warmup_session(session: requests.Session) -> None:
    """GET the search-dashboard page once so Cloudflare issues the __cf_bm cookie."""
    warmup_headers = {**_BROWSER_HEADERS, "Accept": "text/html,application/xhtml+xml,*/*"}
    resp = session.get(_WARMUP_URL, headers=warmup_headers, timeout=30)
    if resp.status_code == 403:
        raise requests.HTTPError(
            "ChemRxiv warmup GET returned 403 -- Cloudflare JS challenge, requests cannot solve this",
            response=resp,
        )
    resp.raise_for_status()


def _resolve_category_id(session: requests.Session, category_name: str) -> str:
    """Resolve a human-readable category name to its ChemRxiv UUID."""
    for url in (_CATEGORIES_URL, _DISCIPLINES_URL):
        resp = session.get(url, timeout=30)
        if resp.status_code == 404:
            continue
        resp.raise_for_status()
        data = resp.json()
        # The API may return a list or a wrapper dict with a named key.
        if isinstance(data, list):
            entries: list[dict] = data
        else:
            entries = data.get("categories", data.get("disciplines", []))
        name_lower = category_name.lower()
        for entry in entries:
            if entry.get("name", "").lower() == name_lower:
                return str(entry["id"])
        available = [e.get("name", "") for e in entries]
        raise ValueError(
            f"Category {category_name!r} not found in {url}. Available names: {available}"
        )
    raise ValueError(
        f"Could not fetch category list for {category_name!r}: "
        "both /categories and /disciplines returned 404"
    )


def _parse_authors(item: dict) -> list[str]:
    authors_raw: list[dict] = item.get("authors") or []
    result: list[str] = []
    for a in authors_raw:
        if "firstName" in a or "lastName" in a:
            first = a.get("firstName", "")
            last = a.get("lastName", "")
            name = f"{first} {last}".strip()
        else:
            name = a.get("name", "").strip()
        if name:
            result.append(name)
    return result


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def fetch_chemrxiv_papers_for_date(date_jst: datetime) -> dict[str, list[Paper]]:
    config = Config()
    papers_by_concept: dict[str, list[Paper]] = {}

    session = requests.Session()
    session.headers.update(_BROWSER_HEADERS)

    # Warm up the session once so Cloudflare issues the __cf_bm cookie.
    _warmup_session(session)

    window_start = (date_jst - timedelta(hours=24)).astimezone(timezone.utc)
    window_end = (date_jst + timedelta(hours=24)).astimezone(timezone.utc)
    search_date_from = window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    search_date_to = window_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    for concept, category_name in config.chemrxiv_concepts.items():
        try:
            category_id = _resolve_category_id(session, category_name)
            params: dict[str, str | int] = {
                "term": "",
                "categoryIds": category_id,
                "searchDateFrom": search_date_from,
                "searchDateTo": search_date_to,
                "sort": "PUBLISHED_DATE_DESC",
                "limit": 50,
                "skip": 0,
            }
            response = session.get(_ITEMS_URL, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching ChemRxiv items for {concept}: {e}")
            raise

        if "itemHits" not in payload:
            raise ValueError(f"ChemRxiv API response missing itemHits key for concept {concept!r}")

        seen: set[str] = set()
        concept_papers: list[Paper] = []

        for hit in payload["itemHits"]:
            item: dict = hit.get("item", hit)

            raw_date = item.get("publishedDate") or item.get("submittedDate")
            parsed_date = _parse_date(raw_date)
            if parsed_date is None:
                logging.warning(f"Skipping ChemRxiv entry with malformed date: {raw_date}")
                continue
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            if abs(date_jst - parsed_date) > timedelta(hours=24):
                continue

            item_id: str = str(item.get("id", ""))
            doi: str = str(item.get("doi", ""))
            if doi:
                link = f"https://doi.org/{doi}"
            else:
                link = f"https://chemrxiv.org/engage/chemrxiv/article-details/{item_id}"

            dedup_key = doi or item_id
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            concept_papers.append(
                Paper(
                    id=doi or item_id,
                    title=str(item.get("title", "")).strip(),
                    link=link,
                    summary=str(item.get("abstract", "")),
                    authors=_parse_authors(item),
                    category=concept,
                    updated=parsed_date.isoformat(),
                )
            )

        if concept_papers:
            papers_by_concept[concept] = concept_papers

    return papers_by_concept
