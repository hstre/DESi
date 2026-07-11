"""Read measured capability scores from the empirical routing_table.json.

Capability (score per task class) is model-intrinsic, so the router should use
the *measured* number whenever a configured model id matches a table entry —
rather than a hand-typed config hint. Cost stays deployment-specific (your
provider's price, from config); only the score is sourced here.

Match is exact on model id. A locally-named model (e.g. ``llama3.1:8b``) that is
not the exact id measured in the table (``meta-llama/llama-3.1-8b-instruct``)
deliberately does NOT inherit the table score — running it locally is a
different deployment, and claiming the measured score would be dishonest.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_TABLE_PATH = Path(__file__).resolve().parent / "routing_table.json"


@lru_cache(maxsize=1)
def _load() -> dict[tuple[str, str], dict]:
    raw = json.loads(_TABLE_PATH.read_text(encoding="utf-8"))
    cells: dict[tuple[str, str], dict] = {}
    for task, info in raw.get("tasks", {}).items():
        for cell in info.get("cells", []):
            cells[(task, cell["model"])] = cell
    return cells


def measured_score(task_class: str, model_id: str) -> float | None:
    cell = _load().get((task_class, model_id))
    return None if cell is None else cell.get("score")


def measured_cell(task_class: str, model_id: str) -> dict | None:
    """The full table cell (score + provenance). A cell re-fitted from ledger evidence carries
    ``score_source: "ledger-refit"`` - callers surface that instead of claiming 'measured'."""
    return _load().get((task_class, model_id))


def has_table() -> bool:
    return _TABLE_PATH.exists()
