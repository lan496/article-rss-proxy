import logging
from pathlib import Path

from feedgen.feed import FeedGenerator

from src.config import Config, TODAY_JST
from src.paper import Paper


def generate_rss_file(
    pushing_papers: list[Paper],
    other_papers: list[Paper],
    xml_path: Path,
    feed_title: str | None = None,
    source_label: str = "arxiv",
    favicon_url: str | None = None,
):
    config = Config()

    fg = FeedGenerator()
    fg.id(config.deploy_url)
    fg.link(href=config.deploy_url, rel="alternate")
    fg.title(feed_title or config.title)
    fg.description(feed_title or config.title)
    fg.language("ja")
    if favicon_url:
        fg.image(url=favicon_url, title=feed_title or config.title, link=config.deploy_url)

    for p in pushing_papers:
        fe = fg.add_entry()
        fe.id(p.id)
        fe.title(p.title)

        fe.link(href=p.link)

        fe.pubDate(p.updated)

        desc_parts = [p.summary]
        if p.fig1:
            desc_parts.append(f'<img src="{p.fig1}"/>')
        if p.authors:
            desc_parts.append("<p>" + ", ".join(p.authors) + "</p>")
        if p.affils:
            desc_parts.append("<p>" + "\n".join(p.affils) + "</p>")
        fe.description("\n\n".join(desc_parts))

    if other_papers:
        fe = fg.add_entry()
        fe.id(f"other-{source_label}-papers-{TODAY_JST.strftime('%Y-%m-%d')}")
        fe.title(f"Other {source_label} papers {TODAY_JST.strftime('%Y-%m-%d')}")
        fe.link(href=f"https://arxiv.org/{TODAY_JST.strftime('%Y-%m-%d')}")  # dummy
        fe.pubDate(TODAY_JST)
        fe.description(
            "<ol>\n<li>"
            + "</li>\n<li>".join([f'<a href="{p.link}">{p.title}</a>' for p in other_papers])
            + "</li>\n</ol>"
        )

    fg.rss_file(xml_path)
    logging.info("RSS written to %s", xml_path)
