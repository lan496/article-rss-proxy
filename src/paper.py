from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Paper:
    id: str
    title: str
    link: str
    summary: str
    category: str
    updated: str
    fig1: str = ""
    authors: list = field(default_factory=list)
    affils: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "category": self.category,
            "updated": self.updated,
            "fig1": self.fig1,
            "authors": self.authors,
            "affils": self.affils,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Paper":
        return cls(
            id=d["id"],
            title=d["title"],
            link=d["link"],
            summary=d["summary"],
            category=d["category"],
            updated=d["updated"],
            fig1=d.get("fig1", ""),
            authors=d.get("authors", []),
            affils=d.get("affils", []),
        )
