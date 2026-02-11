from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo


MAX_NJOBS = 8

# For RSS generation
TODAY_JST = datetime.now(ZoneInfo("Asia/Tokyo"))

# For arXiv fetch
_CATEGORIES = [
    "cond-mat.mtrl-sci",
    "physics.comp-ph",
]

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
    title: str = "lan496/article-rss-proxy/arXiv"
    deploy_url: str = "https://lan496.github.io/article-rss-proxy/"
    categories: list[str] = field(default_factory=lambda: _CATEGORIES)
    interests: str = _INTERESTS
    redirect_alphaxiv: bool = False
