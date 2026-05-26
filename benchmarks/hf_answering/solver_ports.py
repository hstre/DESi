"""Solver ports for the role-separated pipeline (PERIPHERAL).

A solver produces the FINAL verdict. DeepSeek v4 Pro is the semantic solver
(role: deepseek_semantic); any model can also solve directly for the baselines.
The solver NEVER modifies or reinterprets a DESi-core structure — it only reads a
benchmark input or a Granite projection and emits a verdict label. One call, no
retries, no self-consistency voting. Keys in-process; raises if absent.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from desi.live_llm_validation.model_registry import (  # noqa: E402
    ROLE_DEEPSEEK, ROLE_GRANITE, completion_price, model_for_role, prompt_price,
)
from dissent_governance import require_governed  # noqa: E402  (DISSENT_IS_NEVER_AUTHORITY)

# label synonym maps (parsing only — not answer repair)
BOOL_SYNS = {"YES": ("yes", "true", "supported", "correct"),
             "NO": ("no", "false", "incorrect")}
VERIFY_SYNS = {
    "SUPPORTS": ("supports", "support", "supported", "entailment", "entails"),
    "REFUTES": ("refutes", "refute", "refuted", "contradicts", "contradiction", "contradicted"),
    "NOT_ENOUGH_INFO": ("not_enough_info", "not enough info", "not enough information",
                        "nei", "neutral", "insufficient", "not enough"),
}

_DIRECT_BOOL = (
    "Read the passage and answer the question. Reason briefly if needed, then end "
    "your reply with a final line exactly: FINAL: YES  or  FINAL: NO.\n\n"
    "Passage: {context}\n\nQuestion: {primary}\n"
)
_DIRECT_VERIFY = (
    "Decide whether the EVIDENCE supports, refutes, or gives not enough info about "
    "the CLAIM. Reason briefly if needed, then end with a final line exactly: "
    "FINAL: SUPPORTS  or  FINAL: REFUTES  or  FINAL: NOT_ENOUGH_INFO.\n\n"
    "CLAIM: {primary}\n\nEVIDENCE: {context}\n"
)
# Calibrated evidence-style prompt (prompt-only experiment; compact, no CoT,
# no self-reflection). Defines each label explicitly: explicit entailment ->
# SUPPORTS, explicit contradiction -> REFUTES, partial/approximate/silent ->
# NOT_ENOUGH_INFO; absence of contradiction is not support; no outside knowledge.
_DIRECT_VERIFY_CALIBRATED = (
    "Classify the CLAIM using ONLY the EVIDENCE (no outside knowledge).\n"
    "- SUPPORTS: the evidence EXPLICITLY entails the claim (the claim follows "
    "directly and fully from what the evidence states).\n"
    "- REFUTES: the evidence EXPLICITLY contradicts the claim.\n"
    "- NOT_ENOUGH_INFO: the evidence neither explicitly entails nor explicitly "
    "contradicts the claim -- including when the linkage is partial, when numbers "
    "or quantities are approximate or do not settle the claim's exact bound, or "
    "when the evidence is silent on a fact the claim needs. Absence of "
    "contradiction is NOT support.\n"
    "End with a final line exactly: FINAL: SUPPORTS or FINAL: REFUTES or "
    "FINAL: NOT_ENOUGH_INFO.\n\nCLAIM: {primary}\n\nEVIDENCE: {context}\n"
)
# Entailment-direct prompt family (for over-abstention datasets, e.g. NLI/FEVER):
# direct entailment counts as SUPPORTS without demanding exhaustive proof; NEI only
# when the evidence genuinely does not address the claim; contradiction stays strict.
_DIRECT_VERIFY_ENTAILMENT = (
    "Classify the CLAIM using ONLY the EVIDENCE (no outside knowledge).\n"
    "- SUPPORTS: the evidence entails the claim. DIRECT entailment counts even if "
    "the evidence is not exhaustive -- if the evidence states or directly implies "
    "the claim's content, answer SUPPORTS; do not demand a complete or perfect "
    "proof.\n"
    "- REFUTES: the evidence genuinely contradicts the claim (strict: a real "
    "conflict, not a wording mismatch).\n"
    "- NOT_ENOUGH_INFO: ONLY when the evidence does not address the claim or is "
    "truly insufficient to judge -- NOT merely because the wording differs or the "
    "evidence is incomplete. Do NOT abstain when the evidence does entail or "
    "contradict the claim.\n"
    "End with a final line exactly: FINAL: SUPPORTS or FINAL: REFUTES or "
    "FINAL: NOT_ENOUGH_INFO.\n\nCLAIM: {primary}\n\nEVIDENCE: {context}\n"
)
_ROLE_BOOL = (
    "A structured extractor produced this projection of a passage/question. Use it "
    "to answer the question. End with a final line exactly: FINAL: YES or FINAL: NO.\n\n"
    "EXTRACTION: {projection}\n\nQUESTION: {primary}\n"
)
_ROLE_VERIFY = (
    "A structured extractor produced this projection of a claim and its evidence. "
    "Use it to decide the verdict. End with a final line exactly: FINAL: SUPPORTS "
    "or FINAL: REFUTES or FINAL: NOT_ENOUGH_INFO.\n\nEXTRACTION: {projection}\n\n"
    "CLAIM: {primary}\n"
)
_DISSENT_VERIFY = (
    "An extractor produced a STRUCTURE and an epistemic CHALLENGER produced DISSENT "
    "(counter-hypotheses, missing evidence, alternative readings, and whether "
    "NOT_ENOUGH_INFO is plausible). Weigh the dissent honestly: if the challenger "
    "shows the evidence is insufficient or genuinely ambiguous, prefer "
    "NOT_ENOUGH_INFO; do not discard a well-founded challenge. End with a final "
    "line exactly: FINAL: SUPPORTS or FINAL: REFUTES or FINAL: NOT_ENOUGH_INFO.\n\n"
    "STRUCTURE: {projection}\n\nDISSENT: {dissent}\n\nCLAIM: {primary}\n"
)
_DISSENT_BOOL = (
    "An extractor produced a STRUCTURE and a CHALLENGER produced DISSENT. Weigh the "
    "dissent, then answer the question. End with a final line exactly: FINAL: YES "
    "or FINAL: NO.\n\nSTRUCTURE: {projection}\n\nDISSENT: {dissent}\n\nQUESTION: {primary}\n"
)
# Recheck (calibrated dissent): the solver already gave FIRST_VERDICT; an auditor
# flagged gaps. The solver MAY reject the dissent -- NEI is NOT automatic.
_RECHECK_VERIFY = (
    "You first concluded FIRST_VERDICT = {first} for the CLAIM. A dissent auditor "
    "(strength {strength}) noted, ADVISORY and NOT authoritative: {audit}\n\nRules:\n"
    "1. The dissent is advisory, not authoritative.\n"
    "2. A WEAK dissent CANNOT override a first verdict that is directly supported "
    "or refuted by the evidence.\n"
    "3. Switch to NOT_ENOUGH_INFO ONLY IF the dissent identifies a CONCRETE, "
    "claim-relevant MISSING-evidence gap that DEFEATS the first verdict -- not mere "
    "imprecision/approximation, and NOT when the evidence already contradicts the "
    "claim (contradictory evidence keeps REFUTES; only genuinely missing evidence "
    "warrants NOT_ENOUGH_INFO).\n4. Otherwise KEEP your first verdict.\n\n"
    "CLAIM: {primary}\n\nEVIDENCE: {context}\n\nEnd with a final line exactly: "
    "FINAL: SUPPORTS or FINAL: REFUTES or FINAL: NOT_ENOUGH_INFO.\n"
)


def parse_verdict(text: str, syns: dict) -> str | None:
    """Prefer the requested 'FINAL: <LABEL>' line; else the LAST label synonym in
    the text (reasoning models state the conclusion last); else None. Parsing
    only — no repair, no retry."""
    if not text:
        return None
    low = text.strip().lower()
    fin = low.rfind("final:")
    if fin != -1:
        tail = low[fin + len("final:"):]
        for label, ss in syns.items():
            for s in ss:
                if s in tail:
                    return label
    # fallback: last occurrence anywhere
    best_label, best_idx = None, -1
    for label, ss in syns.items():
        for s in ss:
            idx = low.rfind(s)
            if idx > best_idx:
                best_label, best_idx = label, idx
    return best_label


def build_direct_prompt(primary: str, context: str, *, task: str, variant: str = "baseline") -> str:
    if task == "boolq":
        tmpl = _DIRECT_BOOL
    elif variant in ("evidence_strict", "calibrated"):
        tmpl = _DIRECT_VERIFY_CALIBRATED
    elif variant == "entailment_direct":
        tmpl = _DIRECT_VERIFY_ENTAILMENT
    else:
        tmpl = _DIRECT_VERIFY
    return tmpl.format(primary=primary, context=context)


def build_role_prompt(projection: str, primary: str, *, task: str) -> str:
    tmpl = _ROLE_BOOL if task == "boolq" else _ROLE_VERIFY
    return tmpl.format(projection=projection, primary=primary)


def build_dissent_prompt(projection: str, dissent: str, primary: str, *, task: str) -> str:
    tmpl = _DISSENT_BOOL if task == "boolq" else _DISSENT_VERIFY
    return tmpl.format(projection=projection, dissent=dissent, primary=primary)


def build_recheck_prompt(primary: str, context: str, first: str, strength: str, audit: str, *, task: str) -> str:
    # verify-task only (the calibrated-dissent experiment targets 3-class NEI)
    return _RECHECK_VERIFY.format(first=first, strength=strength, audit=audit,
                                  primary=primary, context=context)


class DeepSeekDirectSolver:
    """DeepSeek solver via the direct api.deepseek.com endpoint (much faster than
    the OpenRouter reasoning route). Reads DEEPSEEK_API_KEY in-process. Deterministic
    (temp 0): the answer is never retried. A SINGLE retry is allowed ONLY for a
    transient TLS/5xx network error (the environment's TLS proxy issues certs with
    notBefore~=now, causing a brief 'certificate not yet valid' skew) — this is
    infrastructure resilience, not answer-level retry or voting; the prompt and
    answer are unchanged."""

    _ENDPOINT = "https://api.deepseek.com/chat/completions"

    def __init__(self, *, model: str = "deepseek-chat", max_tokens: int = 384,
                 token_env: str = "DEEPSEEK_API_KEY") -> None:
        import os
        self._key = os.environ.get(token_env)
        if not self._key:
            raise RuntimeError(f"{token_env} not set; direct DeepSeek unavailable.")
        self.model = model
        self.name = f"{model} (direct)"
        self.max_tokens = max_tokens

    def _call(self, prompt: str) -> tuple[str, int, int]:
        import json as _json
        import time as _time
        import urllib.request
        body = _json.dumps({"model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0, "max_tokens": self.max_tokens,
                            "stream": False}).encode("utf-8")
        last = None
        for attempt in range(2):  # one transient-network retry only (not answer retry)
            try:
                req = urllib.request.Request(
                    self._ENDPOINT, data=body,
                    headers={"Authorization": f"Bearer {self._key}",
                             "Content-Type": "application/json"}, method="POST")
                r = _json.load(urllib.request.urlopen(req, timeout=60))
                text = (r["choices"][0]["message"].get("content") or "").strip()
                u = r.get("usage") or {}
                return text, int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
            except Exception as exc:  # transient TLS/5xx skew -> single retry
                last = exc
                if attempt == 0:
                    _time.sleep(2)
        raise RuntimeError(f"deepseek direct call failed: {last!r}")

    def solve_direct(self, primary, context, *, task, variant="baseline"):
        return self._call(build_direct_prompt(primary, context, task=task, variant=variant))

    def solve_projection(self, projection, primary, *, task):
        return self._call(build_role_prompt(projection, primary, task=task))

    def solve_with_dissent(self, projection, dissent, primary, *, task):
        dissent = require_governed(dissent)   # DISSENT_IS_NEVER_AUTHORITY
        return self._call(build_dissent_prompt(projection, dissent, primary, task=task))

    def solve_recheck(self, primary, context, first, strength, audit, *, task):
        audit = require_governed(audit)       # DISSENT_IS_NEVER_AUTHORITY
        return self._call(build_recheck_prompt(primary, context, first, strength, audit, task=task))

    def price(self):
        # deepseek-chat list pricing estimate ($/token): cache-miss in, out
        return (0.27e-6, 1.10e-6)


class Solver:
    """An OpenRouter-backed solver bound to a role/model. Produces a verdict
    either directly from the raw input or from a Granite projection."""

    def __init__(self, role: str, *, max_tokens: int = 384) -> None:
        from desi.live_llm_validation.openrouter_client import api_key_present
        if not api_key_present():
            raise RuntimeError("OPENROUTER_API_KEY not set; solver unavailable.")
        self.role = role
        self.model_id = model_for_role(role)
        self.name = self.model_id
        self.max_tokens = max_tokens

    def _call(self, prompt: str) -> tuple[str, int, int]:
        from desi.live_llm_validation.openrouter_client import chat_completion
        resp = chat_completion(self.model_id, [{"role": "user", "content": prompt}],
                               max_tokens=self.max_tokens, temperature=0.0)
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        u = resp.get("usage") or {}
        return text, int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)

    def solve_direct(self, primary: str, context: str, *, task: str) -> tuple[str, int, int]:
        tmpl = _DIRECT_BOOL if task == "boolq" else _DIRECT_VERIFY
        return self._call(tmpl.format(primary=primary, context=context))

    def solve_projection(self, projection: str, primary: str, *, task: str) -> tuple[str, int, int]:
        tmpl = _ROLE_BOOL if task == "boolq" else _ROLE_VERIFY
        return self._call(tmpl.format(projection=projection, primary=primary))

    def solve_with_dissent(self, projection, dissent, primary, *, task):
        dissent = require_governed(dissent)   # DISSENT_IS_NEVER_AUTHORITY
        return self._call(build_dissent_prompt(projection, dissent, primary, task=task))

    def solve_recheck(self, primary, context, first, strength, audit, *, task):
        audit = require_governed(audit)       # DISSENT_IS_NEVER_AUTHORITY
        return self._call(build_recheck_prompt(primary, context, first, strength, audit, task=task))

    def price(self):
        return (prompt_price(self.model_id), completion_price(self.model_id))


class ConstantSolver:
    """Offline solver: constant verdict (no model, no token). Wiring tests only."""

    def __init__(self, verdict: str = "NO") -> None:
        self.name = f"constant_solver({verdict})"
        self._v = verdict

    def solve_direct(self, primary, context, *, task):
        return f"FINAL: {self._v}", 0, 0

    def solve_projection(self, projection, primary, *, task):
        return f"FINAL: {self._v}", 0, 0

    def solve_with_dissent(self, projection, dissent, primary, *, task):
        require_governed(dissent)             # DISSENT_IS_NEVER_AUTHORITY
        return f"FINAL: {self._v}", 0, 0

    def solve_recheck(self, primary, context, first, strength, audit, *, task):
        require_governed(audit)               # DISSENT_IS_NEVER_AUTHORITY
        return f"FINAL: {self._v}", 0, 0

    def price(self):
        return (0.0, 0.0)


__all__ = [
    "BOOL_SYNS", "VERIFY_SYNS", "ConstantSolver", "DeepSeekDirectSolver",
    "ROLE_DEEPSEEK", "ROLE_GRANITE", "Solver", "build_direct_prompt",
    "build_role_prompt", "parse_verdict",
]
