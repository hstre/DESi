"""DocumentArtifact + corpus indexing — Aufgabe 1.

Read-only enumeration of the v2.x and v3.x documentation surface
plus the rule-patch-protocol papers and the per-version
Abschlussberichte. Each indexed document carries a deterministic
``sha256`` so the audit's downstream phases can prove they saw the
documents at the same byte content.
"""
from __future__ import annotations

import hashlib
import pathlib
from dataclasses import dataclass
from typing import Any


# Document roots the v3.0 audit walks. Each entry is a directory
# (relative to repo root) whose ``*.md`` files are indexed.
DEFAULT_DOC_ROOTS: tuple[str, ...] = (
    "docs/memory",
    "docs/rule_patch_protocol",
)


# The minimal set of documents that constitute the v2.x corpus.
# Used to verify the corpus is intact before claims are extracted.
REQUIRED_MEMORY_DOCS: frozenset[str] = frozenset({
    "v2_0.md", "v2_1.md", "v2_2.md", "v2_3.md", "v2_4.md",
    "v2_5.md", "v2_6.md", "v2_7.md", "v2_8.md", "v2_9.md",
})


REQUIRED_PROTOCOL_DOCS: frozenset[str] = frozenset({
    "README.md",
    "phase_diagram.md",
    "tinkering_vs_science.md",
    "worked_example_v27.md",
    "negative_control.md",
})


@dataclass(frozen=True)
class DocumentArtifact:
    """One indexed markdown document."""

    doc_id: str
    path: str            # relative to repo root
    sha256: str
    line_count: int
    section_count: int   # count of headings starting with '#'

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "path": self.path,
            "sha256": self.sha256,
            "line_count": self.line_count,
            "section_count": self.section_count,
        }


def _doc_id(rel_path: str) -> str:
    h = hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:12]
    return "doc_" + h


def _count_sections(text: str) -> int:
    return sum(
        1 for ln in text.splitlines()
        if ln.lstrip().startswith("#")
    )


def index_document(repo_root: pathlib.Path,
                    rel_path: str) -> DocumentArtifact:
    abs_path = repo_root / rel_path
    raw = abs_path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return DocumentArtifact(
        doc_id=_doc_id(rel_path),
        path=rel_path,
        sha256=hashlib.sha256(raw).hexdigest()[:16],
        line_count=len(text.splitlines()),
        section_count=_count_sections(text),
    )


def index_corpus(
    repo_root: pathlib.Path,
    *,
    roots: tuple[str, ...] = DEFAULT_DOC_ROOTS,
) -> tuple[DocumentArtifact, ...]:
    """Index every ``*.md`` under each root, sorted by rel_path."""
    out: list[DocumentArtifact] = []
    for root in roots:
        base = repo_root / root
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.md")):
            rel = p.relative_to(repo_root).as_posix()
            out.append(index_document(repo_root, rel))
    return tuple(out)


__all__ = [
    "DEFAULT_DOC_ROOTS",
    "DocumentArtifact",
    "REQUIRED_MEMORY_DOCS",
    "REQUIRED_PROTOCOL_DOCS",
    "index_corpus",
    "index_document",
]
