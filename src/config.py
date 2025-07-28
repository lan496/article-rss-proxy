from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo


MAX_NJOBS = 8

# for rss gen
TODAY_JST = datetime.now(ZoneInfo("Asia/Tokyo"))

# for arxiv fetch
_CATEGORIES = [
    "cond-mat.mtrl-sci",
    "physics.comp-ph",
]

# for llm
_INTERESTS = """\
- 対称性の観点から物質の性質を議論する研究
- 結晶構造探索及び相図を計算的に求める研究
- 結晶構造の分類に関する研究
- 固相・液相・気相を問わず、合成可能性・合成レシピを計算化学で設計・予測する研究
- 計算物質科学分野のOpen-source software
\
"""


@dataclass
class Config:
    title: str = "lan496/article-rss-proxy/arXiv"
    deploy_url: str = "https://lan496.github.io/article-rss-proxy/"
    categories: list[str] = field(default_factory=lambda: _CATEGORIES)
    interests: str = _INTERESTS
    translate_ja: bool = False
