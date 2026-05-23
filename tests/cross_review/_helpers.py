"""Pure read-only helpers used by the v3.3 cross-review tests.

No production module is referenced. All work happens on bytes
read from disk under `docs/cross_review/` and `artifacts/v3_3/`.
"""
from __future__ import annotations

import hashlib
import json
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEW_ROOT = REPO_ROOT / "docs" / "cross_review"
CORRUPT_ROOT = REVIEW_ROOT / "corrupted"
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "v3_3"


def sha16(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_results() -> dict:
    return json.loads((ARTIFACT_ROOT / "reviewer_results.json").read_text())


def load_agreement() -> dict:
    return json.loads((ARTIFACT_ROOT / "agreement_report.json").read_text())


def load_corrupted() -> dict:
    return json.loads((ARTIFACT_ROOT / "corrupted_results.json").read_text())


__all__ = [
    "ARTIFACT_ROOT",
    "CORRUPT_ROOT",
    "REPO_ROOT",
    "REVIEW_ROOT",
    "load_agreement",
    "load_corrupted",
    "load_results",
    "sha16",
]
