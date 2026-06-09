"""Deterministic keyword retrieval over a local corpus directory.

Read-only, offline, deterministic: scores ``.txt``/``.md`` files by query-term
hit count (ties broken by filename) and returns the top snippets. No embeddings,
no network — a transparent baseline tool. Bind it to a corpus with
``make_keyword_search(dir)``; it is only registered when a corpus is configured,
so it never pretends to have data it doesn't.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

_WORD = re.compile(r"\w+")


def make_keyword_search(corpus_dir: str | Path, top_k: int = 3) -> Callable[[str], str]:
    root = Path(corpus_dir)

    def search(query: str) -> str:
        terms = {w.lower() for w in _WORD.findall(query)}
        if not terms:
            raise ValueError("empty query")
        files = sorted(
            [p for p in root.rglob("*") if p.suffix.lower() in (".txt", ".md")]
        )
        if not files:
            raise ValueError(f"no corpus documents under {root}")
        scored = []
        for p in files:
            text = p.read_text(encoding="utf-8", errors="ignore")
            tokens = [w.lower() for w in _WORD.findall(text)]
            hits = sum(tokens.count(t) for t in terms)
            if hits:
                scored.append((hits, p.name, text))
        if not scored:
            raise ValueError("no matching documents")
        scored.sort(key=lambda s: (-s[0], s[1]))   # deterministic: hits desc, name asc
        out = []
        for hits, name, text in scored[:top_k]:
            snippet = " ".join(text.split())[:200]
            out.append(f"[{name} · {hits} hits] {snippet}")
        return "\n".join(out)

    return search
