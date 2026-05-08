from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import click
from joblib import delayed, Parallel

from src.arxiv_html_parser import extract_fig1_authors_affils
from src.config import Config, FEED_FAVICONS, MAX_NJOBS, TODAY_JST
from src.fetcher import (
    fetch_aps_papers_for_date,
    fetch_nature_papers_for_date,
    fetch_papers_for_date,
)
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
        logging.info("arXiv: No papers fetched. Writing empty feed.")
        generate_rss_file([], [], DOCS_DIR / "arxiv.xml", favicon_url=FEED_FAVICONS["arxiv"])
        return

    recommended, others = _split_by_recommendation(fetched_papers)
    _enrich_arxiv_papers(recommended)

    generate_rss_file(
        recommended, others, DOCS_DIR / "arxiv.xml", favicon_url=FEED_FAVICONS["arxiv"]
    )


def run_aps_pipeline(date_jst: datetime) -> None:
    papers_by_journal = fetch_aps_papers_for_date(date_jst)
    total = sum(len(ps) for ps in papers_by_journal.values())
    logging.info(f"APS: Fetched {total} papers across {len(papers_by_journal)} journals.")

    if not papers_by_journal:
        logging.info("APS: No papers fetched. Writing empty feeds.")
        for journal in Config().aps_journals:
            generate_rss_file(
                [],
                [],
                DOCS_DIR / f"aps-{journal}.xml",
                feed_title=f"lan496/article-rss-proxy/APS/{journal}",
                source_label=f"aps-{journal}",
                favicon_url=FEED_FAVICONS["aps"],
            )
        return

    # Flatten all papers for a single LLM recommendation pass
    all_papers = [p for ps in papers_by_journal.values() for p in ps]
    are_recommended = recommend_papers(all_papers)
    recommendation_map = {paper.id: rec for paper, rec in zip(all_papers, are_recommended)}
    logging.info(f"APS: Recommend {sum(are_recommended)} papers.")

    # Generate one XML per journal
    for journal, journal_papers in papers_by_journal.items():
        recommended = [p for p in journal_papers if recommendation_map[p.id]]
        others = [p for p in journal_papers if not recommendation_map[p.id]]

        generate_rss_file(
            recommended,
            others,
            DOCS_DIR / f"aps-{journal}.xml",
            feed_title=f"lan496/article-rss-proxy/APS/{journal}",
            source_label=f"aps-{journal}",
            favicon_url=FEED_FAVICONS["aps"],
        )

    # Write empty feeds for configured journals with no fetched papers
    for journal in Config().aps_journals:
        if journal not in papers_by_journal:
            generate_rss_file(
                [],
                [],
                DOCS_DIR / f"aps-{journal}.xml",
                feed_title=f"lan496/article-rss-proxy/APS/{journal}",
                source_label=f"aps-{journal}",
                favicon_url=FEED_FAVICONS["aps"],
            )


def run_nature_pipeline(date_jst: datetime) -> None:
    papers_by_journal = fetch_nature_papers_for_date(date_jst)
    total = sum(len(ps) for ps in papers_by_journal.values())
    logging.info(f"Nature: Fetched {total} papers across {len(papers_by_journal)} journals.")

    if not papers_by_journal:
        logging.info("Nature: No papers fetched. Writing empty feeds.")
        for journal in Config().nature_journals:
            generate_rss_file(
                [],
                [],
                DOCS_DIR / f"nature-{journal}.xml",
                feed_title=f"lan496/article-rss-proxy/Nature/{journal}",
                source_label=f"nature-{journal}",
                favicon_url=FEED_FAVICONS["nature"],
            )
        return

    # Flatten all papers for a single LLM recommendation pass
    all_papers = [p for ps in papers_by_journal.values() for p in ps]
    are_recommended = recommend_papers(all_papers)
    recommendation_map = {paper.id: rec for paper, rec in zip(all_papers, are_recommended)}
    logging.info(f"Nature: Recommend {sum(are_recommended)} papers.")

    # Generate one XML per journal
    for journal, journal_papers in papers_by_journal.items():
        recommended = [p for p in journal_papers if recommendation_map[p.id]]
        others = [p for p in journal_papers if not recommendation_map[p.id]]

        generate_rss_file(
            recommended,
            others,
            DOCS_DIR / f"nature-{journal}.xml",
            feed_title=f"lan496/article-rss-proxy/Nature/{journal}",
            source_label=f"nature-{journal}",
            favicon_url=FEED_FAVICONS["nature"],
        )

    # Write empty feeds for configured journals with no fetched papers
    for journal in Config().nature_journals:
        if journal not in papers_by_journal:
            generate_rss_file(
                [],
                [],
                DOCS_DIR / f"nature-{journal}.xml",
                feed_title=f"lan496/article-rss-proxy/Nature/{journal}",
                source_label=f"nature-{journal}",
                favicon_url=FEED_FAVICONS["nature"],
            )


@click.command()
@click.option("--yymmdd", default=None, help="Date (YYMMDD). Defaults to today.")
@click.option(
    "--pipeline",
    type=click.Choice(["arxiv", "aps", "nature", "all"]),
    default="all",
    help="Which pipeline to run (default: all).",
)
def main(yymmdd: str | None, pipeline: str):
    if yymmdd is None:
        yymmdd = TODAY_JST.strftime("%y%m%d")
        logging.info(f"yymmdd is not specified. Using today: {yymmdd}")

    date_jst = datetime.strptime(yymmdd, "%y%m%d").replace(tzinfo=ZoneInfo("Asia/Tokyo"))

    if pipeline in ("arxiv", "all"):
        run_arxiv_pipeline(date_jst)
    if pipeline in ("aps", "all"):
        run_aps_pipeline(date_jst)
    if pipeline in ("nature", "all"):
        run_nature_pipeline(date_jst)

    tracker.log_summary()


if __name__ == "__main__":
    main()
