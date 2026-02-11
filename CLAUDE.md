# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

article-rss-proxy is a Python tool that creates personalized arXiv RSS feeds. It fetches papers from arXiv, filters them using the Gemini API based on configured research interests, optionally translates abstracts to Japanese, extracts figures/authors/affiliations from paper HTML pages, and generates an RSS feed. A GitHub Actions workflow runs daily to publish the feed to GitHub Pages.

## Commands

```bash
# Install dependencies
uv sync

# Run the pipeline (generates docs/index.xml)
uv run src/main.py
uv run src/main.py --yymmdd 250515   # specific date in YYMMDD format

# Lint and format
ruff check .
ruff format .

# Type checking
mypy src/

# Pre-commit (ruff + mypy + uv lock check)
pre-commit run --all-files
```

## Architecture

The pipeline runs sequentially through five stages, orchestrated by `src/main.py`:

1. **Fetch** (`arxiv_fetcher.py`): Queries arXiv API for papers in configured categories, deduplicates by paper ID. Handles weekday-to-UTC time range mapping (Tuesday fetches from Friday).
2. **Filter** (`llm_utils.py` → `recommend_papers`): Sends papers in batches (size=25) to Gemini API (`gemini-2.5-flash`) to classify as relevant or not, based on `Config.interests`.
3. **Translate** (`llm_utils.py` → `translate_abstract`): Optionally translates abstracts to Japanese via Gemini (`gemini-2.0-flash`). Runs in parallel via joblib.
4. **Parse HTML** (`arxiv_html_parser.py`): Scrapes arXiv HTML pages to extract first figure, author names, and affiliations using BeautifulSoup CSS selectors (`.ltx_personname`, `.ltx_contact`). Runs in parallel via joblib.
5. **Generate RSS** (`rss_generator.py`): Produces an Atom/RSS feed with recommended papers as full entries and remaining papers collated into a single linked list entry.

The `Paper` dataclass (`arxiv_fetcher.py`) flows through all stages, accumulating fields (summary_ja, fig1, authors, affils). `Config` (`config.py`) centralizes all user preferences: arXiv categories, research interests prompt, and translation toggle.

## Key Details

- **Package manager**: uv (lockfile: `uv.lock`)
- **Python**: >=3.12, source in `src/` (flat layout, no package directory)
- **Secrets**: `GEMINI_API_KEY` loaded from `.env` via python-dotenv
- **Rate limiting**: 60-second waits between Gemini API batches; exponential backoff on 429/5xx errors (up to 10 retries)
- **Parallelism**: joblib with `MAX_NJOBS=8` for translation and HTML parsing
- **Output**: `docs/index.xml` (gitignored; deployed to `gh-pages` branch by CI)
- **CI**: GitHub Actions runs daily at 02:17 UTC (11:17 JST), commits output to `gh-pages` branch
- **No test suite**: The project currently has no automated tests
