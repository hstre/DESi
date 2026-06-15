"""Stage A: project each case's source_text into a DESi epistemic state.

This is the ONE place claims are produced. The deterministic SPL backend yields
nothing on free clinical/ops text (it is a toy for structured triples), so real
extraction uses the LLM backend (``desi.spl_adapter.LLMSemanticBackend``) driven
by the existing OpenRouter client. That means extraction is itself a model call
— it runs in CI with the OPENROUTER_API_KEY secret, ONCE per case, and its
output is written to ``frozen/<case>.claims.json`` and hashed. Everything
downstream (slice construction, the four arms) reads those frozen claims, so the
inputs are fixed and reconstructable before any arm runs.

No key, no extraction: the OpenRouter client raises rather than fabricating.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# desi package (src layout) + the OpenRouter client
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from desi.spl_adapter import LLMSemanticBackend, SPLAdapter  # noqa: E402
from desi.live_llm_validation import openrouter_client  # noqa: E402

from case_schema import Case, load_cases  # noqa: E402
from slice_matcher import content_hash_text  # noqa: E402

FROZEN_DIR = Path(__file__).resolve().parent / "frozen"
EXTRACTION_MODEL = "deepseek/deepseek-chat"  # the projection model (not the arm model)


def _make_llm_call(model: str):
    def llm_call(prompt: str) -> str:
        resp = openrouter_client.chat_completion(
            model,
            [{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.0,
        )
        return resp["choices"][0]["message"]["content"]
    return llm_call


def extract_case(case: Case, *, model: str = EXTRACTION_MODEL) -> dict:
    """Project one case's source_text into claims via the LLM SPL backend."""
    adapter = SPLAdapter(backend=LLMSemanticBackend(llm_call=_make_llm_call(model)))
    result = adapter.project_text(
        case.source_text, source="wrong_slice_case", author="extract", document_id=case.case_id
    )
    claims = []
    for c in result.claims:
        claims.append({
            "subject": getattr(c, "subject", ""),
            "predicate": getattr(c, "predicate", ""),
            "object": getattr(c, "object", ""),
            "status": getattr(c, "status", "unknown"),
            "modality": getattr(c, "modality", "hypothesis"),
            "confidence": getattr(c, "confidence", 0.5),
            "generated_by": getattr(c, "generated_by", "") or "llm_semantic_projection",
            "evidence_refs": list(getattr(c, "evidence_refs", []) or []),
        })
    payload = {
        "case_id": case.case_id,
        "extraction_model": model,
        "method": "llm_semantic_projection",
        "n_claims": len(claims),
        "claims": claims,
    }
    payload["claims_hash"] = content_hash_text(
        json.dumps(claims, sort_keys=True, ensure_ascii=False)
    )
    return payload


def main(track: str = "real") -> None:
    out_dir = FROZEN_DIR / track
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = load_cases(track)
    for cid, case in cases.items():
        payload = extract_case(case)
        out = out_dir / f"{cid}.claims.json"
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{cid}: {payload['n_claims']} claims -> {track}/{out.name} (hash {payload['claims_hash'][:12]})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "real")
