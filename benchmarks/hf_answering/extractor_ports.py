"""Extractor ports for the role-separated pipeline (PERIPHERAL).

Granite's role is ONLY structured extraction / projection — never a verdict. The
projection is a small, fixed shape (claims / evidence / polarity / uncertainty);
it invents no ontology and never touches a DESi-core structure. Reads the key
in-process via the existing openrouter_client; raises if absent (never fabricates).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from desi.live_llm_validation.model_registry import ROLE_GRANITE, model_for_role  # noqa: E402

_EXTRACT_PROMPT = (
    "You are a STRUCTURED EXTRACTOR. Do NOT give a verdict or an answer. From the "
    "input below, produce compact JSON with keys: \"claims\" (list of short claim "
    "strings), \"evidence\" (list of short evidence snippets), \"polarity\" (one of "
    "support, refute, mixed, unclear), \"uncertainty\" (one of low, medium, high). "
    "Output ONLY the JSON.\n\nINPUT:\n{input}\n\nJSON:"
)


@dataclass(frozen=True)
class Projection:
    """Minimal structured projection — NOT a DESi-core structure."""
    claims: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    polarity: str = "unclear"
    uncertainty: str = "medium"
    raw: str = ""
    parse_ok: bool = True

    def to_compact(self) -> str:
        return json.dumps({
            "claims": self.claims, "evidence": self.evidence,
            "polarity": self.polarity, "uncertainty": self.uncertainty,
        }, ensure_ascii=False)


def _parse_projection(text: str) -> Projection:
    """Best-effort JSON parse. No repair beyond extracting the first JSON object;
    on failure the raw text is kept as the projection (parse_ok=False)."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(0))
            return Projection(
                claims=[str(c) for c in (d.get("claims") or [])][:8],
                evidence=[str(e) for e in (d.get("evidence") or [])][:8],
                polarity=str(d.get("polarity", "unclear")),
                uncertainty=str(d.get("uncertainty", "medium")),
                raw=text, parse_ok=True,
            )
        except Exception:
            pass
    return Projection(raw=text.strip(), parse_ok=False)


class GraniteExtractor:
    """Granite as a structured extractor (role: granite_structured)."""

    def __init__(self, *, max_tokens: int = 256) -> None:
        from desi.live_llm_validation.openrouter_client import api_key_present
        if not api_key_present():
            raise RuntimeError("OPENROUTER_API_KEY not set; extractor unavailable.")
        self.model_id = model_for_role(ROLE_GRANITE)
        self.name = self.model_id
        self.max_tokens = max_tokens

    def extract(self, input_text: str) -> tuple[Projection, int, int]:
        from desi.live_llm_validation.openrouter_client import chat_completion
        resp = chat_completion(
            self.model_id,
            [{"role": "user", "content": _EXTRACT_PROMPT.format(input=input_text)}],
            max_tokens=self.max_tokens, temperature=0.0,
        )
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        u = resp.get("usage") or {}
        return _parse_projection(text), int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)


class NullExtractor:
    """Offline extractor: passes the input through as the raw projection (no
    model, no token). For pipeline wiring tests only."""

    name = "null_extractor"

    def extract(self, input_text: str) -> tuple[Projection, int, int]:
        return Projection(raw=input_text, parse_ok=False), 0, 0


__all__ = ["GraniteExtractor", "NullExtractor", "Projection"]
