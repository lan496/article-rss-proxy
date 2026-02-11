from __future__ import annotations

import argparse
from datetime import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from joblib import delayed, Parallel

from src.aps_fetcher import fetch_aps_papers_for_date
from src.arxiv_fetcher import fetch_papers_for_date
from src.arxiv_html_parser import extract_fig1_authors_affils
from src.config import MAX_NJOBS, TODAY_JST
from src.llm_utils import recommend_papers
from src.rss_generator import generate_rss_file
from src.usage_tracker import tracker


if TYPE_CHECKING:
    from src.paper import Paper


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DOCS_DIR = Path(__file__).parent.parent / "docs"


def _split_by_recommendation(papers: list[Paper]) -> tuple[list[Paper], list[Paper]]:
    are_recommended = recommend_papers(papers)
    recommended: list[Paper] = []
    others: list[Paper] = []
    for is_recommended, paper in zip(are_recommended, papers):
        if is_recommended:
            recommended.append(paper)
        else:
            others.append(paper)
    logging.info(f"Recommend {len(recommended)} papers.")
    return recommended, others


def _enrich_arxiv_papers(papers: list[Paper]) -> None:
    extracted_results = Parallel(n_jobs=MAX_NJOBS, backend="threading")(
        delayed(extract_fig1_authors_affils)(paper.id) for paper in papers
    )
    for extracted, paper in zip(extracted_results, papers):
        paper.fig1 = extracted["fig1"]
        paper.authors = extracted["authors"] if extracted["authors"] else paper.authors
        paper.affils = extracted["affils"]
    logging.info("Extract Done.")


def run_arxiv_pipeline(date_jst: datetime) -> None:
    fetched_papers = fetch_papers_for_date(date_jst)
    logging.info(f"Fetched {len(fetched_papers)} papers.")

    if not fetched_papers:
        logging.info("arXiv: No papers fetched. Skipping.")
        return

    recommended, others = _split_by_recommendation(fetched_papers)
    _enrich_arxiv_papers(recommended)

    generate_rss_file(recommended, others, DOCS_DIR / "arxiv.xml")


def run_aps_pipeline(date_jst: datetime) -> None:
    fetched_papers = fetch_aps_papers_for_date(date_jst)
    logging.info(f"APS: Fetched {len(fetched_papers)} papers.")

    if not fetched_papers:
        logging.info("APS: No papers fetched. Skipping.")
        return

    recommended, others = _split_by_recommendation(fetched_papers)

    generate_rss_file(
        recommended,
        others,
        DOCS_DIR / "aps.xml",
        feed_title="lan496/article-rss-proxy/APS",
        source_label="aps",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--yymmdd", type=str, default=None, help="Date (YYMMDD). Defaults to today"
    )
    args = parser.parse_args()

    if args.yymmdd is not None:
        yymmdd = args.yymmdd
    else:
        yymmdd = TODAY_JST.strftime("%y%m%d")
        logging.info(f"yymmdd is not specified. Using today: {yymmdd}")

    date_jst = datetime.strptime(yymmdd, "%y%m%d").replace(tzinfo=ZoneInfo("Asia/Tokyo"))

    run_arxiv_pipeline(date_jst)
    run_aps_pipeline(date_jst)

    tracker.log_summary()


if __name__ == "__main__":
    main()
