"""Shared helpers for the v3.24 paper test suite — drift,
contradiction, and reproducibility checks against
``docs/papers/v3_claims.json``."""
from __future__ import annotations

import json
import pathlib
from typing import Any


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_claims() -> list[dict[str, Any]]:
    path = _REPO_ROOT / "docs" / "papers" / "v3_claims.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["claims"])


def load_artifact(name: str) -> dict[str, Any]:
    path = _REPO_ROOT / "artifacts" / name / "report.json"
    return json.loads(path.read_text(encoding="utf-8"))


def navigate(data: dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(
                f"path {path!r} missing at segment {part!r}"
            )
    return cur


def values_equal(a: Any, b: Any) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-5
        except (TypeError, ValueError):
            return False
    if isinstance(a, list) and isinstance(b, list):
        return sorted(a, key=str) == sorted(b, key=str)
    return a == b


__all__ = [
    "load_artifact",
    "load_claims",
    "navigate",
    "values_equal",
]
