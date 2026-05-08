from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo


MAX_NJOBS = 8

FEED_FAVICONS: dict[str, str] = {
    "arxiv": "https://arxiv.org/favicon.ico",
    "aps": "https://cdn.journals.aps.org/development/journals/images/favicon.ico",
    "nature": "https://www.nature.com/uploads/product/npjcompumats/rss.png",
    "chemrxiv": "https://chemrxiv.org/favicon.ico",
}

# For RSS generation
TODAY_JST = datetime.now(ZoneInfo("Asia/Tokyo"))

# For arXiv fetch
_CATEGORIES = [
    "cond-mat.mtrl-sci",
    "physics.comp-ph",
]

# For APS Physical Review fetch
_APS_JOURNALS = ["prb", "prl", "prmaterials", "prx"]

# For Nature journal fetch
_NATURE_JOURNALS = ["npjcompumats"]

# For ChemRxiv concept fetch (label -> ConceptID used by chemrxiv.org search)
_CHEMRXIV_CONCEPTS: dict[str, str] = {
    "theochem": "502565",  # Theoretical and Computational Chemistry
}

# For LLM-based paper filtering
_INTERESTS = """\
- Research discussing material properties from the perspective of symmetry
- Research computationally exploring crystal structures and phase diagrams
- Research on classification of crystal structures
- Research using computational chemistry to design/predict synthesizability and synthesis recipes across solid, liquid, and gas phases
- Open-source software in the computational materials science domain
\
"""


@dataclass
class Config:
    title: str = "article-rss-proxy"
    deploy_url: str = "https://lan496.github.io/article-rss-proxy/"
    categories: list[str] = field(default_factory=lambda: _CATEGORIES)
    interests: str = _INTERESTS
    aps_journals: list[str] = field(default_factory=lambda: _APS_JOURNALS)
    nature_journals: list[str] = field(default_factory=lambda: _NATURE_JOURNALS)
    chemrxiv_concepts: dict[str, str] = field(default_factory=lambda: dict(_CHEMRXIV_CONCEPTS))
