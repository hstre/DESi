"""Shared helpers for v5.5 paper tests."""
from __future__ import annotations

import hashlib
import json
import pathlib


_REPO = pathlib.Path(__file__).resolve().parents[2]
_PAPER_PATH = (
    _REPO / "docs" / "papers"
    / "v5_methodology_transfer_consolidation.md"
)
_CLAIMS_PATH = (
    _REPO / "docs" / "papers" / "v5_claims.json"
)
_ARTIFACT_ROOT = _REPO / "artifacts"


def load_paper_text() -> str:
    return _PAPER_PATH.read_text(encoding="utf-8")


def load_claims() -> list[dict]:
    return json.loads(
        _CLAIMS_PATH.read_text(encoding="utf-8"),
    )["claims"]


def load_artifact(rel: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / rel).read_text(encoding="utf-8"),
    )


def navigate(doc: dict, path: str) -> object:
    parts = path.split(".")
    cur = doc
    for p in parts:
        if isinstance(cur, list):
            cur = cur[int(p)]
        else:
            cur = cur[p]
    return cur


def artifact_hash(rel: str) -> str:
    doc = load_artifact(rel)
    canon = json.dumps(
        doc, sort_keys=True, separators=(",", ":"),
    ).encode()
    return hashlib.sha256(canon).hexdigest()[:16]
