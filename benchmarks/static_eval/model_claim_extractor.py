#!/usr/bin/env python3
"""Model-assisted claim extraction (P3 prototype) with strict JSON output.

Path: prefer **Granite** (HF Inference, structured extractor) → fallback
**DeepSeek V4** (OpenRouter, reasoning) → fallback the rule-based **P2** extractor.
The model is asked for STRICT JSON only (no prose), parsed robustly with a
recovery step; on any failure we fall back. Every result carries provenance:
``extraction_method``, ``extraction_model``, ``fallback_used``, plus parse flags.

Honest scope: this is **not** a semantic-graph parser. It is model-dependent and
can hallucinate triples that are not in the text; treat the output as candidate
claims, not verified facts. Tokens are read from the environment only.

Target schema:
    {"claims": [{"subject","predicate","object","confidence":0-1,
                 "claim_type":"fact|causal|temporal|attribute"}]}
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(_REPO / "benchmarks" / "gaia"))  # for hf_inference_backend

from freetext_claim_extractor import extract_subclaims   # noqa: E402  (P2 fallback)

_CLAIM_TYPES = ("fact", "causal", "temporal", "attribute")
_DEFAULT_GRANITE = "ibm-granite/granite-3.3-8b-instruct"
_DEFAULT_DEEPSEEK = "deepseek/deepseek-v4-pro"
_MAX_TOKENS = 4096

_EXTRACTION_INSTRUCTION = (
    "You extract atomic factual claims from the ANSWER, using the QUESTION only to "
    "resolve ellipsis and pronouns (never to add facts the answer does not assert). "
    "Output ONLY a single JSON object, no prose, no markdown, no code fences. "
    'Schema: {"claims":[{"subject":str,"predicate":str,"object":str,'
    '"confidence":number 0..1,"claim_type":"fact|causal|temporal|attribute",'
    '"negated":bool}]}. Rules: (1) emit at least one claim for any substantive '
    "answer, including SHORT factual answers and sentence fragments — ground the "
    "subject from the QUESTION when the answer is elliptical (Q 'Where is X?' "
    "A 'Paris' -> subject X, predicate 'is located in', object 'Paris'); (2) a bare "
    "'No'/'Yes' answer becomes the QUESTION's proposition with negated=true/false; "
    "(3) split conjunctions, lists and dates into separate claims; (4) represent "
    "negation, modality and causation explicitly; (5) resolve 'it'/'they' to the "
    "entity when unambiguous. Do NOT invent facts not stated or directly implied. "
    'ONLY if the answer is truly empty, UNKNOWN, or a pure refusal, output {"claims":[]}.'
)


# --------------------------------------------------------------------------- #
# JSON parsing + recovery
# --------------------------------------------------------------------------- #
def _coerce_claim(c: dict) -> dict | None:
    if not isinstance(c, dict):
        return None
    subj = str(c.get("subject", "")).strip()
    pred = str(c.get("predicate", "")).strip()
    obj = str(c.get("object", "")).strip()
    if not (subj or pred or obj):
        return None
    try:
        conf = float(c.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    conf = min(1.0, max(0.0, conf))
    ctype = str(c.get("claim_type", "fact")).strip().lower()
    if ctype not in _CLAIM_TYPES:
        ctype = "fact"
    return {"subject": subj, "predicate": pred, "object": obj,
            "confidence": round(conf, 3), "claim_type": ctype}


def parse_claims_json(content: str) -> tuple[list[dict] | None, str]:
    """Return (claims, how) where how in {'ok','recovery'} or (None,'failed')."""
    if not content:
        return None, "failed"

    def _try(text: str):
        try:
            data = json.loads(text)
        except Exception:
            return None
        claims = data.get("claims") if isinstance(data, dict) else None
        if not isinstance(claims, list):
            return None
        out = [c for c in (_coerce_claim(x) for x in claims) if c]
        return out

    direct = _try(content.strip())
    if direct is not None:
        return direct, "ok"
    # Recovery: strip code fences, then take the outermost {...} block.
    cleaned = re.sub(r"```(?:json)?|```", "", content).strip()
    rec = _try(cleaned)
    if rec is not None:
        return rec, "recovery"
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        rec = _try(m.group(0))
        if rec is not None:
            return rec, "recovery"
    return None, "failed"


# --------------------------------------------------------------------------- #
# Backend calls
# --------------------------------------------------------------------------- #
def _call_granite(text: str, model: str) -> tuple[str, dict]:
    from hf_inference_backend import chat_answer_with_meta
    return chat_answer_with_meta(text, model=model, instruction=_EXTRACTION_INSTRUCTION,
                                 max_tokens=_MAX_TOKENS, temperature=0.0)


def _call_deepseek(text: str, model: str) -> tuple[str, dict]:
    from desi.live_llm_validation.openrouter_client import chat_completion
    resp = chat_completion(
        model,
        [{"role": "system", "content": _EXTRACTION_INSTRUCTION},
         {"role": "user", "content": text}],
        max_tokens=_MAX_TOKENS, temperature=0.0,
    )
    choice = resp["choices"][0]
    content = (choice["message"].get("content") or "").strip()
    meta = {"finish_reason": choice.get("finish_reason"),
            "provider_returned_model": resp.get("model"),
            "provider": resp.get("provider")}
    return content, meta


def _p2_fallback(text: str, question: str = "") -> list[dict]:
    # P24: with a question, use the question-grounded rule extractor so short /
    # elliptical / yes-no answers still yield atomic claims (visibility, not truth).
    if question:
        try:
            from p24_extractor_recall import rule_extract
            grounded = rule_extract(question, text)
            if grounded:
                for c in grounded:
                    c.setdefault("confidence", 0.5)
                return grounded
        except Exception:
            pass
    claims = []
    for sc in extract_subclaims(text):
        ctype = "temporal" if sc.kind == "year" else "fact"
        claims.append({"subject": sc.subject, "predicate": sc.text,
                       "object": "", "confidence": 0.5, "claim_type": ctype})
    return claims


def _hf_token() -> bool:
    return bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN"))


def _openrouter_key() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def extract_claims_model(text: str, *, backend: str = "auto",
                         granite_model: str | None = None,
                         deepseek_model: str = _DEFAULT_DEEPSEEK,
                         question: str = "") -> dict:
    """Extract claims via the model path (prefer Granite, then DeepSeek, then P2).

    P24: ``question`` is passed to the model so elliptical / short / yes-no answers
    can be grounded (and to the rule-based fallback)."""
    granite_model = granite_model or os.environ.get("HF_INFERENCE_MODEL") or _DEFAULT_GRANITE
    model_input = f"QUESTION: {question}\nANSWER: {text}" if question else text
    attempts: list[dict] = []

    def _result(claims, method, model, parse_how, meta=None):
        return {
            "claims": claims,
            "extraction_method": method,
            "extraction_model": model,
            "fallback_used": method != "granite",
            "json_recovery_used": parse_how == "recovery",
            "raw_json_ok": parse_how == "ok",
            "attempts": attempts,
            "provider_meta": meta or {},
            "n_claims": len(claims),
        }

    order = []
    if backend in ("auto", "granite"):
        order.append("granite")
    if backend in ("auto", "granite", "deepseek"):
        order.append("deepseek")

    for stage in order:
        try:
            if stage == "granite":
                if not _hf_token():
                    attempts.append({"stage": "granite", "model": granite_model,
                                     "result": "no HF token"})
                    continue
                content, meta = _call_granite(model_input, granite_model)
                model_id = granite_model
            else:
                if not _openrouter_key():
                    attempts.append({"stage": "deepseek", "model": deepseek_model,
                                     "result": "no OPENROUTER_API_KEY"})
                    continue
                content, meta = _call_deepseek(model_input, deepseek_model)
                model_id = deepseek_model
        except Exception as exc:
            attempts.append({"stage": stage, "model": granite_model if stage == "granite"
                             else deepseek_model, "result": f"call_failed: {exc!r}"[:160]})
            continue
        claims, how = parse_claims_json(content)
        if claims is not None:
            attempts.append({"stage": stage, "model": model_id, "result": f"parsed:{how}",
                             "n": len(claims)})
            return _result(claims, stage, model_id, how, meta)
        attempts.append({"stage": stage, "model": model_id, "result": "json_parse_failed"})

    # Final fallback: rule-based P2.
    return _result(_p2_fallback(text, question), "rule_based_p2", None, "failed")


__all__ = ["extract_claims_model", "parse_claims_json"]


if __name__ == "__main__":
    demo = "Virginia Woolf was born in London in 1882 and became a famous writer."
    print(json.dumps(extract_claims_model(demo), indent=2, ensure_ascii=False))
