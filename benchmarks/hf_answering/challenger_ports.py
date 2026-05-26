"""Challenger ('wild brother') ports for the dissent pipeline (PERIPHERAL).

Nemotron-3-Super's role is the epistemic CHALLENGER: it actively seeks
counter-hypotheses, missing evidence, and alternative readings, and judges
whether NOT_ENOUGH_INFO is plausible. It NEVER gives a final verdict. The dissent
is a small fixed shape; it invents no ontology and never touches a DESi-core
structure. Reads the key in-process via openrouter_client; raises if absent.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

NEMOTRON = "nvidia/nemotron-3-super-120b-a12b:free"

# Nemotron-3-Super is a heavy reasoner and truncates structured JSON within a
# reasonable token budget, so we ask for free-text dissent plus a parseable final
# line (like the solver's FINAL:), which survives long reasoning.
_CHALLENGE_PROMPT = (
    "You are an epistemic CHALLENGER ('wild brother'). Do NOT give a final "
    "verdict. Attack overconfident reasoning about the CLAIM given the EVIDENCE "
    "and the extractor STRUCTURE: briefly list counter-hypotheses, missing "
    "evidence, and alternative readings. Then decide whether NOT_ENOUGH_INFO is "
    "plausible and end with a final line EXACTLY: NEI_PLAUSIBLE: YES  or  "
    "NEI_PLAUSIBLE: NO.\n\nCLAIM: {primary}\n\nEVIDENCE: {context}\n\n"
    "STRUCTURE: {structure}\n"
)


@dataclass(frozen=True)
class Dissent:
    """Free-text dissent + a parsed NEI-plausibility flag — NOT a DESi-core
    structure. nei_plausible defaults False and is set True only when the
    challenger explicitly says so (never invented)."""
    nei_plausible: bool = False
    raw: str = ""
    parse_ok: bool = True

    def to_compact(self, *, limit: int = 700) -> str:
        body = " ".join(self.raw.split())[:limit]
        return f"nei_plausible={self.nei_plausible}; dissent={body}"


def _parse_dissent(text: str) -> Dissent:
    """Parse the final 'NEI_PLAUSIBLE: YES/NO' line; the rest is free-text dissent
    passed verbatim to the solver. No JSON, no repair."""
    if not text:
        return Dissent(raw="", parse_ok=False)
    low = text.lower()
    idx = low.rfind("nei_plausible")
    if idx != -1:
        tail = low[idx:]
        if "yes" in tail[:40]:
            return Dissent(nei_plausible=True, raw=text, parse_ok=True)
        if "no" in tail[:40]:
            return Dissent(nei_plausible=False, raw=text, parse_ok=True)
    return Dissent(raw=text.strip(), parse_ok=False)


class NemotronChallenger:
    """Nemotron-3-Super as the epistemic challenger (via OpenRouter, free tier)."""

    def __init__(self, *, max_tokens: int = 768) -> None:
        from desi.live_llm_validation.openrouter_client import api_key_present
        if not api_key_present():
            raise RuntimeError("OPENROUTER_API_KEY not set; challenger unavailable.")
        self.model_id = NEMOTRON
        self.name = NEMOTRON
        self.max_tokens = max_tokens

    def challenge(self, primary: str, context: str, structure: str) -> tuple[Dissent, int, int]:
        from desi.live_llm_validation.openrouter_client import chat_completion
        prompt = _CHALLENGE_PROMPT.format(primary=primary, context=context, structure=structure)
        resp = chat_completion(self.model_id, [{"role": "user", "content": prompt}],
                               max_tokens=self.max_tokens, temperature=0.0)
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        u = resp.get("usage") or {}
        return _parse_dissent(text), int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)

    def price(self):
        return (0.0, 0.0)  # :free


class NullChallenger:
    """Offline challenger: no dissent (nei_plausible=False). Wiring tests only."""

    name = "null_challenger"

    def challenge(self, primary, context, structure):
        return Dissent(raw="", parse_ok=False), 0, 0

    def price(self):
        return (0.0, 0.0)


__all__ = ["Dissent", "NEMOTRON", "NemotronChallenger", "NullChallenger"]
