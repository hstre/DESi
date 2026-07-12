"""Blind prompt + parser for the HARD benchmark (neutral ids, scattered pairs)."""
from __future__ import annotations

import json
import re

from ..failure_modes import Flag
from .items import HARD_ITEMS

# Scattered order so near-miss pairs are never adjacent and clean/failure alternate.
_ORDER = ("H05", "H11", "H02", "H09", "H13", "H01", "H07",
          "H04", "H12", "H06", "H14", "H03", "H10", "H08")

_RUBRIC = """You are a scientific background reviewer. For each excerpt below, decide which of \
the following epistemic problems (if any) are clearly present. An excerpt may have none, one, or \
several. Raise a flag ONLY when the problem is clearly present in THIS text; well-formed text gets \
an empty list. Over-flagging is an error, and so is missing a real problem.

Flags:
- untraceable_citation: the text asserts something is established/supported but names no specific, \
checkable source or passage (vague appeals like "studies show" or "the literature confirms" count \
as untraceable).
- source_domain_mismatch: a claim is grounded in a source whose field cannot bear it (e.g. a \
geophysics or materials-science source used to support an economic or legal claim).
- self_sealing: the conclusion is framed so that every possible outcome — including the opposite \
result — is read as confirmation, with no outcome allowed to count against it.
- overclaim: the conclusion goes beyond what the stated evidence supports (e.g. a tiny single \
sample used to assert a universal law).
- heuristic_not_empirical: a self-constructed, uncalibrated formula/index is presented or used as \
if its value were a measured empirical result.

Judge each excerpt on its own text. Return ONLY a JSON object mapping each excerpt id to a list of \
flags (use [] for none), e.g. {"N1": ["overclaim","untraceable_citation"], "N2": []}. JSON only."""


def neutral_map() -> dict[str, str]:
    """neutral id (N1..) -> item id. Private to the scoring side."""
    return {f"N{i + 1}": iid for i, iid in enumerate(_ORDER)}


def build_prompt() -> str:
    by_id = {it.id: it for it in HARD_ITEMS}
    lines = [_RUBRIC, "", "Excerpts:"]
    for i, iid in enumerate(_ORDER):
        lines.append(f'\nN{i + 1}: "{by_id[iid].text}"')
    return "\n".join(lines)


def parse_answer(text: str) -> dict[str, set[Flag]]:
    known = {f.value: f for f in Flag}
    nmap = neutral_map()
    m = re.search(r"\{.*\}", (text or "").strip(), flags=re.DOTALL)
    obj = {}
    if m:
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            obj = {}
    out: dict[str, set[Flag]] = {}
    for nid, iid in nmap.items():
        raw = obj.get(nid, []) if isinstance(obj, dict) else []
        out[iid] = {known[s] for s in raw if isinstance(s, str) and s in known} \
            if isinstance(raw, list) else set()
    return out


__all__ = ["build_prompt", "neutral_map", "parse_answer"]
