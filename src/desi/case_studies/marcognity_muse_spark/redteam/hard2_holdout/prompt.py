"""Blind, batched prompt for the hold-out.

Granite-4.1-8b's calibrated evidence peak is k*=10 (Appendix D.2). To keep the model
inside its calibrated range, excerpts are presented in batches of at most 10 per call
(``BATCH_SIZE = 9``), never all at once. Order is scattered so paraphrase/near-miss
items do not sit adjacent and rarely share a batch. Neutral ids per batch; a private
id map on the scoring side. Same 8-flag rubric as hard2.
"""
from __future__ import annotations

import json
import re

from ..hard2.items import Flag2
from ..hard2.prompt import _RUBRIC
from .items import HOLDOUT_ITEMS

BATCH_SIZE = 9  # <= granite-4.1-8b k*=10, keeps it inside its calibrated evidence band

# scattered global order (paraphrases/near-misses kept apart and split across batches)
_ORDER = ("H01", "H14", "H21", "H08", "H17", "H05", "H23", "H11", "H26",
          "H03", "H19", "H06", "H27", "H10", "H22", "H15", "H02", "H09",
          "H18", "H04", "H24", "H12", "H07", "H20", "H13", "H25", "H16")


def _batches() -> list[list[str]]:
    return [list(_ORDER[i:i + BATCH_SIZE]) for i in range(0, len(_ORDER), BATCH_SIZE)]


def build_prompts() -> list[tuple[str, dict[str, str]]]:
    """One (prompt_text, neutral_id -> item_id) pair per batch."""
    by_id = {it.id: it for it in HOLDOUT_ITEMS}
    out = []
    for batch in _batches():
        id_map = {f"N{i + 1}": iid for i, iid in enumerate(batch)}
        lines = [_RUBRIC, "", "Excerpts:"]
        for nid, iid in id_map.items():
            lines.append(f'\n{nid}: "{by_id[iid].text}"')
        out.append(("\n".join(lines), id_map))
    return out


def parse_answer(text: str, id_map: dict[str, str]) -> dict[str, set[Flag2]]:
    known = {f.value: f for f in Flag2}
    m = re.search(r"\{.*\}", (text or "").strip(), flags=re.DOTALL)
    obj = {}
    if m:
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            obj = {}
    out: dict[str, set[Flag2]] = {}
    for nid, iid in id_map.items():
        raw = obj.get(nid, []) if isinstance(obj, dict) else []
        out[iid] = {known[s] for s in raw if isinstance(s, str) and s in known} \
            if isinstance(raw, list) else set()
    return out


__all__ = ["BATCH_SIZE", "build_prompts", "parse_answer"]
