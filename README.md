# article-rss-proxy

[![Daily RSS update](https://github.com/lan496/article-rss-proxy/actions/workflows/arxiv_rss.yml/badge.svg)](https://github.com/lan496/article-rss-proxy/actions/workflows/arxiv_rss.yml)

A tool that fetches papers from arXiv, APS (American Physical Society), Nature journals, and ChemRxiv, filters them by research interests using Gemini, and distributes them as RSS feeds.

## Features

- Fetch papers from arXiv categories, APS Physical Review journals (PRB, PRL, PR Materials, PRX), Nature journals (npj Computational Materials), and ChemRxiv (via the Crossref API)
- Filter papers by research interests using the Gemini API
- Extract figures, authors, and affiliations from arXiv papers
- Generate per-source RSS feeds (GitHub Pages)
- Automatic daily updates via GitHub Actions (11:17 JST)

## Setup

```bash
# Install dependencies
uv sync

# Set up environment variables
# Copy .env.example to .env and set your GEMINI_API_KEY
cp .env.example .env
# Edit the .env file to configure your API key
```

## Usage

```bash
# Generate all RSS feeds
uv run src/main.py
# Outputs docs/arxiv.xml, docs/aps-prb.xml, docs/nature-npjcompumats.xml, docs/chemrxiv.xml, etc.

# Run a specific pipeline only
uv run src/main.py --pipeline arxiv
uv run src/main.py --pipeline aps
uv run src/main.py --pipeline nature
uv run src/main.py --pipeline chemrxiv
```

## Deploying with GitHub Pages

1. Create a gh-pages branch

2. In the repository Settings > Pages, configure:
   - Source: Deploy from a branch
   - Branch: gh-pages
   - Folder: /docs

3. Once configured, the RSS feeds will be available at the URLs listed below.

## RSS Feed URLs

| Feed | Source | URL |
|------|--------|-----|
| arXiv | cond-mat.mtrl-sci, physics.comp-ph | https://lan496.github.io/article-rss-proxy/arxiv.xml |
| APS PRB | Physical Review B | https://lan496.github.io/article-rss-proxy/aps-prb.xml |
| APS PRL | Physical Review Letters | https://lan496.github.io/article-rss-proxy/aps-prl.xml |
| APS PR Materials | Physical Review Materials | https://lan496.github.io/article-rss-proxy/aps-prmaterials.xml |
| APS PRX | Physical Review X | https://lan496.github.io/article-rss-proxy/aps-prx.xml |
| Nature npj Comput Mater | npj Computational Materials | https://lan496.github.io/article-rss-proxy/nature-npjcompumats.xml |
| ChemRxiv | ChemRxiv preprints (all subjects, via Crossref) | https://lan496.github.io/article-rss-proxy/chemrxiv.xml |

## Automatic Updates

By default, GitHub Actions runs an automatic update daily at 11:17 JST (02:17 UTC).
Adjust the schedule or filter criteria in `.github/workflows/arxiv_rss.yml` as needed.
