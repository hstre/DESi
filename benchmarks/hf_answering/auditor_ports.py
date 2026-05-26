"""Calibrated dissent-AUDITOR port (PERIPHERAL).

Nemotron Nano's role is a CONTROLLED dissent auditor: it names concrete missing
evidence / overreach and classifies the claim-evidence gap, emitting a dissent
STRENGTH (NONE / WEAK / MEDIUM / STRONG). It does NOT give a verdict and does NOT
force NOT_ENOUGH_INFO -- the solver decides on recheck. A free reasoning model
that often truncates: an unparseable audit degrades SAFELY to strength NONE (no
dissent), so it can never cause an all-NEI collapse. Reads the key in-process via
openrouter_client; raises if absent. Invents no ontology; never a core structure.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

NANO = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
STRENGTHS = ("NONE", "WEAK", "MEDIUM", "STRONG")

_AUDIT_PROMPT = (
    "You are a DISSENT AUDITOR. Do NOT give a verdict and do NOT decide "
    "SUPPORTS/REFUTES/NOT_ENOUGH_INFO. In at most 3 sentences, name any CONCRETE "
    "missing evidence and any overreach in concluding about the CLAIM from the "
    "EVIDENCE, and classify the claim-evidence gap. Then end with EXACTLY one "
    "line: DISSENT_STRENGTH: NONE or WEAK or MEDIUM or STRONG (NONE if the "
    "evidence is sufficient).\n\nCLAIM: {primary}\n\nEVIDENCE: {context}\n\n"
    "EXTRACTOR STRUCTURE: {structure}\n"
)


@dataclass(frozen=True)
class Audit:
    strength: str = "NONE"      # one of STRENGTHS; NONE = no dissent (safe default)
    raw: str = ""
    parse_ok: bool = True

    def to_compact(self, *, limit: int = 600) -> str:
        body = " ".join(self.raw.split())[:limit]
        return f"strength={self.strength}; gaps={body}"


def _parse_audit(text: str) -> Audit:
    """Parse the final DISSENT_STRENGTH line. Unparseable -> NONE (safe; never
    invents a strength)."""
    if not text:
        return Audit(strength="NONE", raw="", parse_ok=False)
    low = text.lower()
    idx = low.rfind("dissent_strength")
    if idx != -1:
        tail = low[idx:idx + 50]
        for s in ("strong", "medium", "weak", "none"):
            if s in tail:
                return Audit(strength=s.upper(), raw=text, parse_ok=True)
    return Audit(strength="NONE", raw=text.strip(), parse_ok=False)


class NanoAuditor:
    def __init__(self, *, max_tokens: int = 1200) -> None:
        from desi.live_llm_validation.openrouter_client import api_key_present
        if not api_key_present():
            raise RuntimeError("OPENROUTER_API_KEY not set; auditor unavailable.")
        self.model_id = NANO
        self.name = NANO
        self.max_tokens = max_tokens

    def audit(self, primary: str, context: str, structure: str) -> tuple[Audit, int, int]:
        from desi.live_llm_validation.openrouter_client import chat_completion
        prompt = _AUDIT_PROMPT.format(primary=primary, context=context, structure=structure)
        resp = chat_completion(self.model_id, [{"role": "user", "content": prompt}],
                               max_tokens=self.max_tokens, temperature=0.0)
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        u = resp.get("usage") or {}
        return _parse_audit(text), int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)

    def price(self):
        return (0.0, 0.0)  # :free


class NullAuditor:
    """Offline auditor: always NONE (no dissent). Wiring tests only."""
    name = "null_auditor"

    def audit(self, primary, context, structure):
        return Audit(strength="NONE", raw="", parse_ok=False), 0, 0

    def price(self):
        return (0.0, 0.0)


__all__ = ["Audit", "NANO", "STRENGTHS", "NanoAuditor", "NullAuditor"]
