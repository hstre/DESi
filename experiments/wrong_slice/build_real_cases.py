"""Generate track-A (real) cases from the committed live-capture corpus.

Source of truth: ``src/desi/live_llm_validation/captures/deepseek_tasks.json``
(and siblings) — real, hashed multi-LLM artifacts. For each fact-dependent
reasoning task we:

  * split the REAL captured prompt into source_text (the facts/statements DESi
    extracts its state from) and task_prompt (the question);
  * derive minimal, case-specific expected answer markers (correctness signal:
    a wrong slice lacks these facts, so it cannot produce the marker);
  * attach provenance (capture file, per-model content_hash, models that ran it).

The splitting/markers are a transparent segmentation of REAL text — not invented
cases. Provenance ties every case back to the captured artifacts. Offline.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURES = HERE.parent.parent / "src" / "desi" / "live_llm_validation" / "captures"
OUT = HERE / "cases_real"

# explicit, transparent derivation per real task (facts | question | markers).
DERIVATIONS = {
    "ds_audit_tension": {
        "domain": "financial_audit",
        "source_text": ("A company reports strong cash generation. Its operating cashflow "
                        "excludes one-off receipts. Its revenue includes early-recognised "
                        "deferred amounts."),
        "task_prompt": ("Name the cashflow tension and the revenue-recognition tension an "
                        "auditor should flag, in two short sentences."),
        "expected_markers": ["cash flow", "cashflow", "revenue recognition", "deferred"],
        "permuted_donor": "ds_multihop", "plausible_donor": "ds_narrative_conflict",
    },
    "ds_narrative_conflict": {
        "domain": "financial_audit",
        "source_text": ("A footnote states receivables overdue more than 90 days increased "
                        "materially. The narrative states collections accelerated versus prior year."),
        "task_prompt": "State the conflict between the footnote and the narrative.",
        "expected_markers": ["overdue", "collection"],
        "permuted_donor": "ds_multihop", "plausible_donor": "ds_complex_conflict",
    },
    "ds_complex_conflict": {
        "domain": "financial_audit",
        "source_text": ("The financial statements are formally correct; the numbers add up. "
                        "Management describes a clearly one-off gain as 'sustainable core growth'."),
        "task_prompt": "Identify the semantic red flag.",
        "expected_markers": ["one-off", "recurring", "sustainable core growth"],
        "permuted_donor": "ds_multihop", "plausible_donor": "ds_evidence_gap",
    },
    "ds_evidence_gap": {
        "domain": "financial_audit",
        "source_text": ("A paper claims the method generalizes across datasets. The paper "
                        "reports evidence on only one dataset."),
        "task_prompt": "What evidence is missing, and should the claim be accepted as stated?",
        "expected_markers": ["additional dataset", "more dataset", "multiple dataset",
                             "other dataset", "second dataset"],
        "permuted_donor": "ds_multihop", "plausible_donor": "ds_audit_tension",
    },
    "ds_multihop": {
        "domain": "multihop_qa",
        "source_text": ("The author of book B was born in city X. City X is the capital of "
                        "country K."),
        "task_prompt": ("In what country is the capital of the country where the author of "
                        "book B was born? List the reasoning hops explicitly."),
        "expected_markers": ["country k"],
        "permuted_donor": "ds_audit_tension", "plausible_donor": "ds_evidence_gap",
    },
}


def _provenance(task_id: str) -> dict:
    prov = {"captures": [], "models": set()}
    for f in sorted(CAPTURES.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for c in data.get("captures", []):
            if c.get("task_id") == task_id:
                prov["captures"].append({
                    "file": f.name,
                    "content_hash": c.get("content_hash", ""),
                    "model_version": c.get("model_version", ""),
                })
                prov["models"].add(c.get("model_version", ""))
    prov["models"] = sorted(prov["models"])
    return prov


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for task_id, d in DERIVATIONS.items():
        prov = _provenance(task_id)
        if not prov["captures"]:
            print(f"SKIP {task_id}: no capture found")
            continue
        case = {
            "case_id": task_id,
            "track": "real",
            "domain": d["domain"],
            "pass_id": "assessment",
            "source_text": d["source_text"],
            "task_prompt": d["task_prompt"],
            "permuted_donor": d["permuted_donor"],
            "plausible_donor": d["plausible_donor"],
            "expected_markers": d["expected_markers"],
            "provenance": prov,
            "notes": (f"Track A (real). Derived from captured task {task_id!r} "
                      f"(models: {', '.join(prov['models'])}). source_text/task split is a "
                      "transparent segmentation of the real captured prompt."),
        }
        (OUT / f"{task_id}.json").write_text(
            json.dumps(case, indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1
        print(f"wrote {task_id}.json  (models: {', '.join(prov['models'])})")
    print(f"{written} real cases -> {OUT}")


if __name__ == "__main__":
    main()
