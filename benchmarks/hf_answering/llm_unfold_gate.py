"""Small-LLM unfolding GATE (PERIPHERAL, benchmark adapter).

A small, cheap LLM (Granite 4.1-8b via OpenRouter) decides ONLY whether the
downstream solver should UNFOLD (treat the claim/evidence link strictly) or
DO_NOT_UNFOLD (treat it as a direct match), or report UNCERTAIN. It runs ONLY on
the ambiguous residue the deterministic layers could not resolve.

HARD CONSTRAINTS (enforced by design):
  * the gate NEVER emits SUPPORTS / REFUTES / NOT_ENOUGH_INFO -- only the 3
    routing decisions below;
  * one call, no retries, no voting, no self-consistency, no chain-of-thought,
    no benchmark-specific prompt; temperature 0; small token budget;
  * key read in-process from OPENROUTER_API_KEY; never written to disk.

Decision meaning:
  UNFOLD         -> evidence partial / ambiguous / missing-linkage -> evidence-strict
  DO_NOT_UNFOLD  -> evidence direct / compact -> entailment-direct
  UNCERTAIN      -> keep the deterministic route (baseline fallback)

It does NOT import or modify the DESi core.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from models import GRANITE, _PRICE  # noqa: E402

DECISIONS = ("UNFOLD", "DO_NOT_UNFOLD", "UNCERTAIN")

_INSTRUCTION = (
    "You are an UNFOLDING GATE for a fact-checking router. You do NOT decide whether "
    "the claim is true, supported, refuted, or has not enough info -- never output "
    "those. You ONLY decide how the downstream solver should treat the link between "
    "the CLAIM and the EVIDENCE:\n"
    "- UNFOLD: the evidence only partially covers the claim, is ambiguous, or is "
    "missing a key link, so the solver should check entailment strictly.\n"
    "- DO_NOT_UNFOLD: the evidence directly and compactly covers the claim, so the "
    "solver may treat it as a direct entailment.\n"
    "- UNCERTAIN: you cannot tell from the evidence alone.\n\n"
    "CLAIM: {claim}\n\nEVIDENCE: {evidence}\n\n"
    "Deterministic signals -> coverage={cov}, entity_overlap={ent}, "
    "category={category}, proposed_route={route}\n\n"
    "Respond with ONLY this JSON and nothing else:\n"
    '{{"decision": "UNFOLD" | "DO_NOT_UNFOLD" | "UNCERTAIN", "reason": "<= 12 words"}}'
)

_JSON_RE = re.compile(r"\{.*?\}", re.DOTALL)


@dataclass(frozen=True)
class GateResult:
    decision: str          # one of DECISIONS (UNCERTAIN on any failure)
    reason: str
    parse_ok: bool
    error: bool            # True if the network call failed (safe-degraded to UNCERTAIN)
    prompt_tokens: int
    completion_tokens: int


class LLMUnfoldGate:
    """Granite-backed unfold/no-unfold gate. One call, no retry, temp 0."""

    def __init__(self, *, model: str = GRANITE, max_tokens: int = 96) -> None:
        from desi.live_llm_validation.openrouter_client import api_key_present
        if not api_key_present():
            raise RuntimeError("OPENROUTER_API_KEY not set; LLM unfold gate unavailable.")
        self.model = model
        self.name = model
        self.max_tokens = max_tokens
        self._price = _PRICE.get(model) or (0.0, 0.0)

    def _parse(self, text: str) -> tuple[str, str, bool]:
        m = _JSON_RE.search(text or "")
        if m:
            try:
                obj = json.loads(m.group(0))
                d = str(obj.get("decision", "")).strip().upper()
                if d in DECISIONS:
                    return d, str(obj.get("reason", ""))[:120], True
            except Exception:
                pass
        # fallback: bare keyword scan (still parse-degraded)
        up = (text or "").upper()
        for d in ("DO_NOT_UNFOLD", "UNFOLD", "UNCERTAIN"):
            if d in up:
                return d, "keyword-parsed", False
        return "UNCERTAIN", "unparseable", False

    def decide(self, claim, evidence, *, cov, ent, category, route) -> GateResult:
        from desi.live_llm_validation.openrouter_client import chat_completion
        prompt = _INSTRUCTION.format(claim=claim, evidence=evidence, cov=cov,
                                     ent=ent, category=category, route=route)
        try:  # ONE call, no retry, no voting
            resp = chat_completion(self.model, [{"role": "user", "content": prompt}],
                                   max_tokens=self.max_tokens, temperature=0.0)
            choices = resp.get("choices") or []
            text = (choices[0]["message"].get("content") or "") if choices else ""
            u = resp.get("usage") or {}
            pt, ct = int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
        except Exception:
            return GateResult("UNCERTAIN", "network-error", False, True, 0, 0)
        decision, reason, ok = self._parse(text)
        return GateResult(decision, reason, ok, False, pt, ct)

    def price(self):
        return self._price


# decision -> solver policy. UNCERTAIN defers to the deterministic route.
def gate_policy(decision: str, deterministic_route: str) -> str:
    if decision == "UNFOLD":
        return "evidence_strict"
    if decision == "DO_NOT_UNFOLD":
        return "entailment_direct"
    return deterministic_route  # UNCERTAIN


__all__ = ["DECISIONS", "GateResult", "LLMUnfoldGate", "gate_policy"]
