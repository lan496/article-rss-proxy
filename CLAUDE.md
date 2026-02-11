# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

article-rss-proxy is a Python tool that creates personalized RSS feeds from academic paper sources. It fetches papers from arXiv and APS (American Physical Society) journals, filters them using the Gemini API based on configured research interests, extracts figures/authors/affiliations from arXiv HTML pages, and generates per-source RSS feeds. A GitHub Actions workflow runs daily to publish the feeds to GitHub Pages.

## Commands

```bash
# Install dependencies
uv sync

# Run all pipelines (generates docs/arxiv.xml, docs/aps-*.xml)
uv run src/main.py
uv run src/main.py --yymmdd 250515          # specific date in YYMMDD format
uv run src/main.py --pipeline arxiv          # arXiv only
uv run src/main.py --pipeline aps            # APS journals only

# Lint and format
ruff check .
ruff format .

# Type checking
mypy src/

# Pre-commit (ruff + mypy + uv lock check)
pre-commit run --all-files
```

## Architecture

`src/main.py` orchestrates two independent pipelines (arXiv and APS), selectable via `--pipeline`.

### arXiv Pipeline (`run_arxiv_pipeline`)

1. **Fetch** (`fetcher/arxiv_fetcher.py`): Queries arXiv API for papers in configured categories, deduplicates by paper ID. Handles weekday-to-UTC time range mapping (Tuesday fetches from Friday).
2. **Filter** (`llm_utils.py` → `recommend_papers`): Sends papers in batches (size=25) to Gemini API (`gemini-2.5-flash`) to classify as relevant or not, based on `Config.interests`.
3. **Parse HTML** (`arxiv_html_parser.py`): Scrapes arXiv HTML pages to extract first figure, author names, and affiliations using BeautifulSoup CSS selectors (`.ltx_personname`, `.ltx_contact`). Runs in parallel via joblib.
4. **Generate RSS** (`rss_generator.py`): Produces `docs/arxiv.xml`.

### APS Pipeline (`run_aps_pipeline`)

1. **Fetch** (`fetcher/aps_fetcher.py`): Fetches RSS feeds from APS Physical Review journals (PRB, PRL, PR Materials, PRX), parses entries via feedparser, filters by publication date.
2. **Filter** (`llm_utils.py` → `recommend_papers`): Single LLM pass across all journals for recommendation.
3. **Generate RSS** (`rss_generator.py`): Produces one XML per journal (`docs/aps-{journal}.xml`).

### Shared

The `Paper` dataclass (`paper.py`) flows through all stages, accumulating fields (fig1, authors, affils). `Config` (`config.py`) centralizes all user preferences: arXiv categories, APS journals, and research interests prompt.

## Key Details

- **Package manager**: uv (lockfile: `uv.lock`)
- **Python**: >=3.12, source in `src/` (flat layout, no package directory)
- **Secrets**: `GEMINI_API_KEY` loaded from `.env` via python-dotenv
- **Rate limiting**: 60-second waits between Gemini API batches; exponential backoff on 429/5xx errors (up to 10 retries)
- **Parallelism**: joblib with `MAX_NJOBS=8` for translation and HTML parsing
- **Output**: `docs/arxiv.xml`, `docs/aps-*.xml` (gitignored; deployed to `gh-pages` branch by CI)
- **CI**: GitHub Actions runs daily at 02:17 UTC (11:17 JST), commits output to `gh-pages` branch
- **No test suite**: The project currently has no automated tests
