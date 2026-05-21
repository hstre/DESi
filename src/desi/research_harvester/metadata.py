"""v27.0 - paper metadata.

Imports only the metadata fields permitted in v27 (title,
abstract, authors, date, categories, paper id) - no full text.
Every fixture paper is explicitly flagged synthetic except the
one real anchor (the base paper), so nothing here can be mistaken
for a fabricated real citation.
"""
from __future__ import annotations

from dataclasses import dataclass

from .taxonomy import is_source, is_topic_area


@dataclass(frozen=True)
class PaperMetadata:
    paper_id: str
    title: str
    abstract: str
    authors: tuple[str, ...]
    date: str
    categories: tuple[str, ...]
    source: str
    is_synthetic: bool

    def __post_init__(self) -> None:
        if not is_source(self.source):
            raise ValueError(f"unknown source: {self.source}")
        for c in self.categories:
            if not is_topic_area(c):
                raise ValueError(f"unknown category: {c}")

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": list(self.authors),
            "date": self.date,
            "categories": list(self.categories),
            "source": self.source,
            "is_synthetic": self.is_synthetic,
        }


__all__ = [
    "PaperMetadata",
]
