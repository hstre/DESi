"""Build a BLIND reviewer prompt and parse the reviewer's answer.

To fill the external slot honestly, a real reviewer must be scored *blind* — it must
see the excerpts and a neutral rubric, but NOT the answer key (which flag each probe
should get). This module:

- builds a reviewer prompt with **neutral excerpt ids** (E1..En) in a fixed,
  interleaved order (so the two clean controls are not positionally obvious) and the
  five flag definitions only — no ``must_flag``, no ``applicable_flags``, no
  "failure/control" labels;
- keeps a private id→probe-key map so the answer can be scored;
- parses a reviewer's JSON answer (keyed by the neutral ids) back into the
  ``{probe_key: [flag, ...]}`` shape the ``ExternalReviewer`` consumes.

The same prompt can be sent to any reviewer (a Claude subagent here, or a real API
model, or Claude Science if it becomes available).
"""
from __future__ import annotations

import json
import re

from .failure_modes import PROBES, Flag

# Fixed, interleaved presentation order (controls C1/C2 are NOT last). Deterministic.
_ORDER = (
    "P2-domain", "C1-clean-citation", "P4-overclaim", "P1-untraceable",
    "P5-heuristic", "C2-clean-heuristic", "P3-selfsealing",
)


def _by_key() -> dict:
    return {p.key: p for p in PROBES}


def neutral_map() -> dict[str, str]:
    """neutral id (E1..) -> probe key. The scoring side keeps this; the reviewer never sees it."""
    return {f"E{i + 1}": key for i, key in enumerate(_ORDER)}


_RUBRIC = """You are a scientific background reviewer. For each excerpt below, decide which of \
the following epistemic problems (if any) are clearly present. Raise a flag ONLY when the problem \
is clearly present; a clean, well-formed excerpt must get an empty list. Over-flagging is an error.

Flags:
- untraceable_citation: something is asserted as verified/supported, but no specific, checkable \
source or passage is named (a bare database name is not a source).
- source_domain_mismatch: a claim is "verified" against a source from the wrong field (e.g. a \
biomedical database used to support a claim in legal philosophy).
- self_sealing: the conclusion is framed so that every possible outcome — success AND failure — \
confirms it, with no stated condition that would disconfirm it.
- overclaim: the conclusion goes beyond what the evidence supports (e.g. one uncontrolled instance \
stated as an "empirically demonstrated" or "intrinsic" general law).
- heuristic_not_empirical: a self-constructed formula/model is presented or used as if it were a \
measured/empirical result, though it has no derivation or calibration.

Judge each excerpt on its own. Return ONLY a JSON object mapping each excerpt id to a list of \
flags (use [] for none), e.g. {"E1": ["overclaim"], "E2": []}. No prose, JSON only."""


def build_prompt() -> str:
    by_key = _by_key()
    lines = [_RUBRIC, "", "Excerpts:"]
    for i, key in enumerate(_ORDER):
        p = by_key[key]
        lines.append(f'\n{f"E{i + 1}"}: "{p.snippet}"')
    return "\n".join(lines)


def parse_answer(text: str) -> dict[str, list[str]]:
    """Extract the JSON object from a reviewer's reply and map neutral ids -> probe keys.

    Unknown flag strings are dropped. Missing ids default to no flags. Returns
    ``{probe_key: [flag_value, ...]}``.
    """
    known = {f.value for f in Flag}
    nmap = neutral_map()
    obj = _extract_json_object(text)
    out: dict[str, list[str]] = {}
    for nid, key in nmap.items():
        raw = obj.get(nid, []) if isinstance(obj, dict) else []
        flags = [s for s in raw if isinstance(s, str) and s in known] if isinstance(raw, list) else []
        out[key] = sorted(set(flags))
    return out


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    # tolerate ```json fences and surrounding prose
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


__all__ = ["build_prompt", "neutral_map", "parse_answer"]
