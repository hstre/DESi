"""Blind prompt + parser for HARD2 (8 flags, neutral ids, scattered pairs)."""
from __future__ import annotations

import json
import re

from .items import HARD2_ITEMS, Flag2

_ORDER = ("G03", "G14", "G09", "G16", "G01", "G12", "G05", "G18", "G15",
          "G08", "G02", "G11", "G06", "G13", "G04", "G17", "G10", "G07")

_RUBRIC = """You are a scientific background reviewer. For each excerpt below, decide which of \
the following epistemic problems (if any) are clearly present. An excerpt may have none, one, or \
several. Raise a flag ONLY when the problem is clearly present in THIS text; well-formed text gets \
an empty list. Over-flagging is an error, and so is missing a real problem.

Flags:
- untraceable_citation: asserts something is established/supported but names no specific, checkable \
source or passage (vague appeals like "studies show", "our earlier reports", "first principles").
- source_domain_mismatch: a claim is grounded in a source whose field/object cannot bear it (e.g. \
rodent-learning effect sizes used for human moral judgment).
- self_sealing: the conclusion is framed so that every outcome — including the opposite result — is \
read as confirmation, with no outcome allowed to count against it.
- overclaim: the conclusion goes beyond what the stated evidence supports (e.g. a post-hoc subgroup \
used to recommend a drug for all patients).
- heuristic_not_empirical: a self-constructed, uncalibrated (or circularly calibrated) formula/index \
is presented or used as if its value were an objective empirical measurement.
- causal_overreach: associational/observational or cross-sectional evidence is stated as causal, or \
a correlation is used to justify an intervention ("X is associated with Y, so changing X will change Y").
- significance_not_importance: statistical significance (a p-value) is conflated with effect size or \
practical/clinical importance ("p < 0.001, so the effect is large / far more effective").
- base_rate_neglect: a screening or conditional-probability claim ignores the base rate (e.g. a very \
accurate test for a rare condition, where most positives are false positives).

Judge each excerpt on its own text. Return ONLY a JSON object mapping each excerpt id to a list of \
flags (use [] for none), e.g. {"N1": ["causal_overreach"], "N2": []}. JSON only."""


def neutral_map() -> dict[str, str]:
    return {f"N{i + 1}": iid for i, iid in enumerate(_ORDER)}


def build_prompt() -> str:
    by_id = {it.id: it for it in HARD2_ITEMS}
    lines = [_RUBRIC, "", "Excerpts:"]
    for i, iid in enumerate(_ORDER):
        lines.append(f'\nN{i + 1}: "{by_id[iid].text}"')
    return "\n".join(lines)


def parse_answer(text: str) -> dict[str, set[Flag2]]:
    known = {f.value: f for f in Flag2}
    nmap = neutral_map()
    m = re.search(r"\{.*\}", (text or "").strip(), flags=re.DOTALL)
    obj = {}
    if m:
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            obj = {}
    out: dict[str, set[Flag2]] = {}
    for nid, iid in nmap.items():
        raw = obj.get(nid, []) if isinstance(obj, dict) else []
        out[iid] = {known[s] for s in raw if isinstance(s, str) and s in known} \
            if isinstance(raw, list) else set()
    return out


__all__ = ["build_prompt", "neutral_map", "parse_answer"]
