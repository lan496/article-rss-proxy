# article-rss-proxy

A tool that fetches papers from arXiv, filters and translates them using Gemini, and distributes them as an RSS feed.

## Features

- Fetch papers from specified arXiv categories via the arXiv API
- Filter papers by research interests using the Gemini API
- Extract figures, authors, and affiliations from papers
- Distribute as an RSS feed (GitHub Pages)
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
# Generate the RSS feed
uv run src/main.py
# Outputs docs/index.xml
```

## Deploying with GitHub Pages

1. Create a gh-pages branch

2. In the repository Settings > Pages, configure:
   - Source: Deploy from a branch
   - Branch: gh-pages
   - Folder: /docs

3. Once configured, the RSS feed will be available at:
   `https://<user>.github.io/article-rss-proxy/index.xml`

## Automatic Updates

By default, GitHub Actions runs an automatic update daily at 11:17 JST (02:17 UTC).
Adjust the schedule or filter criteria in `.github/workflows/arxiv_rss.yml` as needed.
