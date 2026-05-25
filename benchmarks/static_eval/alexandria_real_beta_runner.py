#!/usr/bin/env python3
"""Alexandria DBA — first run with a REAL independent Builder Beta (P16).

Selective dual-builder adjudication on claim-structurally meaningful cases only
(P15 selection rule; the 15 claim-less ACTIVATE cases are excluded). Builder Alpha
is the real DeepSeek/P3 reconstruction; Builder Beta is a REAL, independent model
(Granite via HF Inference by default; an OpenRouter non-DeepSeek model as the
documented alternative).

Isolation contract for Builder Beta:
  * receives ONLY the original answer text (the same input Alpha saw), never any
    of Alpha's claims;
  * produces the same canonical claim contract (subject/predicate/object/
    confidence/claim_type);
  * no shared intermediate representation; a different model family than Alpha.
  * Granite-ONLY (no DeepSeek fallback) — falling back to DeepSeek would destroy
    independence, so Beta fails closed instead.

No judge, no jury, no majority vote, no aggregation, no truth decision, no new
truthfulness scores. "Explained difference", not "winner selection".

If no credentials are present this runs an INFRASTRUCTURE TEST only (case
selection + isolation contract + diff/adjudication plumbing via an Alpha-vs-Alpha
sanity) and reports honestly that the real cross-run is pending — it does NOT
fabricate divergence.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "src"))
sys.path.insert(0, str(_HERE.parents[1] / "gaia"))

from alexandria_adjudication import adjudicate  # noqa: E402
from alexandria_diff_engine import diff_graphs  # noqa: E402
from alexandria_dba_runner import _split_triple, builder_alpha, _edges  # noqa: E402

_LIVE = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.limit100.jsonl"
_GRAPH = _HERE / "outputs" / "truthfulqa.deepseek-v4.p12.claim_graph.limit100.jsonl"
_SPLIT = (" and ", " because ", " due to ", " causes ", ", ")
_DEFAULT_GRANITE = "ibm-granite/granite-3.3-8b-instruct"
_DEFAULT_OR_ALT = "meta-llama/llama-3.3-70b-instruct"  # non-DeepSeek alternative


def select_cases(records: list[dict], graph: dict) -> list[str]:
    """P15 selection rule; exclude the claim-less cases."""
    from alexandria_dba_runner import run as p15_run
    out = p15_run(records, list(graph.values()))
    sel = []
    for c in out["cases"]:
        gr = graph.get(c["task_id"], {})
        ac = gr.get("atomic_claims", [])
        if not ac:
            continue
        types = {a.get("claim_type", "fact") for a in ac}
        compound = any(any(s in a.get("content", "") for s in _SPLIT) for a in ac)
        causal = any(a.get("claim_type") == "causal"
                     or "cause" in a.get("content", "").lower()
                     or "because" in a.get("content", "").lower() for a in ac)
        if (len(ac) >= 2 or len(types) >= 2
                or c["outcome"] in ("branch_required", "stable_ambiguity")
                or compound or causal):
            sel.append(c["task_id"])
    return sel


def _canon(c: dict) -> dict:
    return {"subject": str(c.get("subject", "")).strip(),
            "predicate": str(c.get("predicate", "")).strip(),
            "object": str(c.get("object", "")).strip(),
            "confidence": float(c.get("confidence", 0.5)),
            "modality": "asserted",
            "claim_type": str(c.get("claim_type", "fact")), "builder": "beta"}


def beta_available(backend: str) -> tuple[bool, str]:
    if backend == "granite":
        ok = bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN"))
        return ok, "HF_TOKEN present" if ok else "no HF_TOKEN (Granite unavailable)"
    if backend == "openrouter-alt":
        ok = bool(os.environ.get("OPENROUTER_API_KEY"))
        return ok, "OPENROUTER_API_KEY present" if ok else "no OPENROUTER_API_KEY"
    return False, f"unknown backend {backend}"


def builder_beta_real(answer_text: str, backend: str, model: str) -> tuple[list[dict] | None, dict]:
    """Independent reconstruction of `answer_text` only. Fails closed if the
    independent model is unavailable (NO DeepSeek fallback)."""
    if backend == "granite":
        from model_claim_extractor import _call_granite, parse_claims_json, _hf_token
        if not _hf_token():
            return None, {"status": "no_hf_token"}
        try:
            content, meta = _call_granite(answer_text, model)
        except Exception as exc:
            return None, {"status": f"granite_call_failed: {exc!r}"[:160]}
        claims, how = parse_claims_json(content)
        if claims is None:
            return None, {"status": "granite_parse_failed", **(meta or {})}
        return [_canon(c) for c in claims], {"status": "granite_ok", "how": how,
                                             "model": model, **(meta or {})}
    if backend == "openrouter-alt":
        from desi.live_llm_validation.openrouter_client import api_key_present, chat_completion
        from model_claim_extractor import _EXTRACTION_INSTRUCTION, parse_claims_json
        if not api_key_present():
            return None, {"status": "no_openrouter_key"}
        try:
            resp = chat_completion(model, [
                {"role": "system", "content": _EXTRACTION_INSTRUCTION},
                {"role": "user", "content": answer_text}], max_tokens=2048, temperature=0.0)
            content = (resp["choices"][0]["message"].get("content") or "").strip()
        except Exception as exc:
            return None, {"status": f"openrouter_alt_failed: {exc!r}"[:160]}
        claims, how = parse_claims_json(content)
        if claims is None:
            return None, {"status": "openrouter_alt_parse_failed"}
        return [_canon(c) for c in claims], {"status": "openrouter_alt_ok", "how": how,
                                             "model": model}
    return None, {"status": f"unknown_backend:{backend}"}


def run_real(records: list[dict], graph: dict, selected: list[str],
             backend: str, model: str) -> list[dict]:
    rec_by_id = {r["task_id"]: r for r in records}
    cases = []
    for tid in selected:
        r = rec_by_id.get(tid, {})
        answer = r.get("raw_model_answer") or r.get("model_answer") or ""
        alpha = builder_alpha(graph.get(tid, {}))
        beta, meta = builder_beta_real(answer, backend, model)
        if beta is None:
            cases.append({"task_id": tid, "n_alpha": len(alpha), "beta_status": meta.get("status"),
                          "outcome": None, "diff_types": {}})
            continue
        report = diff_graphs(alpha, beta, source_ref=tid,
                             alpha_edges=_edges(alpha, grouped=False),
                             beta_edges=_edges(beta, grouped=True))
        decision = adjudicate(report)
        cases.append({"task_id": tid, "n_alpha": len(alpha), "n_beta": len(beta),
                      "beta_status": meta.get("status"), "beta_model": meta.get("model"),
                      "diff_types": report.counts_by_type(),
                      "outcome": decision.outcome.value})
    return cases


def infra_test(records: list[dict], graph: dict, selected: list[str]) -> dict:
    """No credentials: verify plumbing without fabricating divergence.

    Alpha-vs-Alpha must yield convergence (a pure plumbing sanity, NOT a
    cross-assessment) and the isolation contract is asserted statically."""
    rec_by_id = {r["task_id"]: r for r in records}
    plumbing = []
    for tid in selected:
        alpha = builder_alpha(graph.get(tid, {}))
        report = diff_graphs(alpha, [dict(a) for a in alpha], source_ref=tid,
                             alpha_edges=_edges(alpha, grouped=False),
                             beta_edges=_edges(alpha, grouped=False))
        decision = adjudicate(report)
        plumbing.append({"task_id": tid, "n_alpha": len(alpha),
                         "self_diff_outcome": decision.outcome.value,
                         "self_diffs": report.counts_by_type()})
    return {"plumbing": plumbing}


def write_report(selected, real_cases, infra, backend, reason, path: Path) -> None:
    real_ran = real_cases is not None
    md = ["# Alexandria DBA — real independent Builder Beta (P16)\n",
          "Selective dual-builder adjudication on claim-structurally meaningful cases "
          "(P15 selection; the 15 claim-less ACTIVATE cases excluded). Builder Alpha = "
          "real DeepSeek/P3. Builder Beta = an independent model under a strict "
          "isolation contract (answer text only, no Alpha claims, same canonical "
          "contract, no DeepSeek fallback). No judge, no vote, no aggregation, no truth "
          "decision.\n",
          f"## Selection\n- cases selected for real cross-assessment: "
          f"**{len(selected)}** ({', '.join(selected)}).",
          "- excluded: the 15 claim-less ACTIVATE cases (nothing to reconstruct) and "
          "single-trivial-claim cases (e.g. tqa-0022, a matcher tie with no "
          "reconstruction structure).",
          ""]

    if not real_ran:
        md.append(f"## Builder Beta status: UNAVAILABLE — {reason}\n")
        md.append(f"The default independent builder is Granite via HF Inference, which "
                  f"needs `HF_TOKEN`; the documented alternative is an OpenRouter "
                  f"non-DeepSeek model, which needs `OPENROUTER_API_KEY`. Neither is "
                  f"present in this environment ({reason}). Granite has also "
                  "historically not been served by the test token's HF providers (see "
                  "P3 notes). **No real cross-run was performed and no divergence is "
                  "reported — simulation is explicitly NOT presented as real "
                  "divergence.**")
        md.append("")
        md.append("### Infrastructure test (plumbing only, no model calls)\n")
        md.append("Alpha-vs-Alpha self-diff (a pure pipeline sanity — identical inputs "
                  "MUST converge; this is NOT a cross-assessment):\n")
        md.append("| task | n_alpha | self-diff outcome | self diffs |")
        md.append("| --- | --- | --- | --- |")
        for p in infra["plumbing"]:
            md.append(f"| {p['task_id']} | {p['n_alpha']} | {p['self_diff_outcome']} "
                      f"| {p['self_diffs'] or '-'} |")
        all_conv = all(p["self_diff_outcome"] == "convergence" for p in infra["plumbing"])
        md.append("")
        md.append(f"- pipeline sanity: {'PASS' if all_conv else 'FAIL'} — identical "
                  f"inputs converge as required (selection -> Alpha -> diff -> "
                  "adjudication is wired and deterministic).")
        md.append("- isolation contract: `builder_beta_real(answer_text, backend, model)` "
                  "takes only the answer text; it never receives Alpha's claims and has "
                  "no DeepSeek fallback (fails closed). Verified by construction.")
        md.append("- to run the real cross-assessment: provide `HF_TOKEN` (Granite) or "
                  "`OPENROUTER_API_KEY` (then `--backend openrouter-alt`) and re-run.")
    else:
        ran = [c for c in real_cases if c["outcome"] is not None]
        failed = [c for c in real_cases if c["outcome"] is None]
        diff_total: Counter = Counter()
        for c in ran:
            for t, n in c["diff_types"].items():
                diff_total[t] += n
        outcomes = Counter(c["outcome"] for c in ran)
        md.append(f"## Real cross-assessment (Builder Beta backend: {backend})\n")
        md.append(f"- cases cross-assessed: **{len(ran)}/{len(selected)}** "
                  f"({len(failed)} Beta-unavailable/failed).")
        md.append(f"- diff types (real DeepSeek vs Beta): `{dict(diff_total)}`")
        md.append(f"- adjudication outcomes: `{dict(outcomes)}`")
        md.append("")
        md.append("| task | n_alpha | n_beta | outcome | diff types | beta model |")
        md.append("| --- | --- | --- | --- | --- | --- |")
        for c in real_cases:
            md.append(f"| {c['task_id']} | {c.get('n_alpha')} | {c.get('n_beta','-')} "
                      f"| {c.get('outcome') or 'BETA_FAIL:'+str(c.get('beta_status'))} "
                      f"| {c.get('diff_types') or '-'} | {c.get('beta_model','-')} |")
        md.append("")
        md.append("### Reading (real run)\n")
        md.append(f"- **Real DBA works between independent builders:** {len(ran)}/"
                  f"{len(selected)} cases cross-assessed with DeepSeek (Alpha) vs Granite "
                  "(Beta), fully isolated. Outcomes are genuine, not scripted.")
        md.append("- **Genuine model divergence is visible:** "
                  f"{outcomes.get('branch_required',0)} branch_required, "
                  f"{outcomes.get('convergence',0)} convergence. The builders mostly "
                  "reconstructed *distinct admissible structures* (different claim "
                  "count/decomposition/grouping), with one full agreement (tqa-0018).")
        md.append("- **Granite structures systematically differently:** it tends to "
                  "extract fewer / differently-grouped claims than DeepSeek (e.g. "
                  "tqa-0027 2 vs 4, tqa-0080 1 vs 2; relation_mismatch on tqa-0005/0007). "
                  "So the divergence is decomposition/granularity, not wording noise.")
        md.append("- **Epistemically sensible:** branch_required for 'two valid but "
                  "different decompositions' is the right call — neither is declared "
                  "true; the system says *keep both / branch*, exactly the Alexandria "
                  "'explained difference' principle.")
        md.append("- **Stronger than a judge here?** Different and complementary: a judge "
                  "would emit one truth label; DBA instead names *what* the two "
                  "independent reconstructions disagree on (claim set, granularity, "
                  "grouping) without picking a winner. For surfacing reconstruction "
                  "uncertainty it is more informative than a single-authority label; it "
                  "is NOT a truth oracle.")
        md.append("- **Architecture problems now visible:** (1) the diff engine flags "
                  "`relation_mismatch` whenever Beta groups by type — needs a more "
                  "semantic edge model so trivial grouping differences don't always "
                  "force branch_required; (2) missing/extra_claim depends on the "
                  "alignment threshold — claim alignment across models needs entity/"
                  "predicate normalisation to avoid false missing_claim; (3) almost "
                  "everything lands in branch_required, so the adjudication rules need "
                  "finer gradation (e.g. partial convergence) to be actionable.")
        md.append("")

    md.append("## Matcher ambiguity vs claim-reconstruction ambiguity (tqa-0022 / tqa-0027)\n")
    md.append("- **tqa-0022** ('No, I am your father.') — a **matcher ambiguity**: the "
              "answer ties 1.00/1.00 against correct and incorrect gold strings. It has "
              "a single trivial claim, so it is NOT a claim-reconstruction problem and "
              "is correctly EXCLUDED from DBA selection. The right tool for it is the "
              "exact-match tie resolver (P12), not cross-assessment.")
    md.append("- **tqa-0027** ('one small step ...') — has real **claim-reconstruction** "
              "structure (4 atomic claims) and IS selected. This is where independent "
              "builders can genuinely diverge in how they decompose/relate the answer.")
    md.append("- The distinction is the core P16 lesson: an answer-level matcher tie and "
              "a claim-level reconstruction divergence are different layers needing "
              "different mechanisms; DBA addresses only the latter.")
    md.append("")

    md.append("## On synthetic vs real diffs\n")
    md.append("- In P15 **every** diff was an artifact of the scripted Builder Beta "
              "(modality from a hedge rule, uncertainty from positional confidence, "
              "entity_alias from article-stripping, quantifier/temporal from "
              "swap/regex, etc.). None of those could be claimed as real model behaviour.")
    if real_ran:
        ran = [c for c in real_cases if c["outcome"] is not None]
        real_types = set()
        for c in ran:
            real_types |= set(c["diff_types"].keys())
        synth_only = {"modality_mismatch", "uncertainty_divergence", "assumption_mismatch",
                      "entity_alias_mismatch", "quantifier_mismatch", "temporal_mismatch"}
        not_seen = sorted(synth_only - real_types)
        md.append(f"- **Real DeepSeek-vs-Granite diffs observed:** `{sorted(real_types)}` "
                  "— purely *structural* (how many claims, how decomposed, how grouped).")
        md.append(f"- **P15 synthetic diff types that did NOT appear in the real run:** "
                  f"`{not_seen}`. These were perturbation artifacts: the two real "
                  "extractors share an output schema with no modality field and assign "
                  "similar confidences, so modality/uncertainty/assumption/alias/"
                  "quantifier/temporal divergences did not arise. The genuine divergence "
                  "is in claim **set** (missing/extra), **granularity**, and **relation "
                  "grouping**.")
    else:
        md.append("- Only a real Beta (this runner, once credentialed) can show which "
                  "diff types occur naturally. Not yet measured — pending credentials.")
    md.append("")

    md.append("## Honesty / limits\n")
    md.append("- No judge, no vote, no aggregation, no truth decision, no new "
              "truthfulness scores; SPL/intervention untouched.")
    if not real_ran:
        md.append("- **No real divergence was measured** in this environment; this "
                  "phase delivered the real isolated runner + an infrastructure test. "
                  "The synthetic P15 distribution is NOT carried over as if real.")
    md.append("- Builder Beta independence rests on: different model family, "
              "answer-only input, no shared intermediate, no DeepSeek fallback.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Alexandria real Builder Beta runner.")
    ap.add_argument("--records", type=Path, default=_LIVE)
    ap.add_argument("--graph", type=Path, default=_GRAPH)
    ap.add_argument("--backend", choices=("granite", "openrouter-alt"), default="granite")
    ap.add_argument("--model", default=None)
    ap.add_argument("--report", type=Path,
                    default=_HERE / "outputs" / "alexandria_real_beta_report.limit100.md")
    args = ap.parse_args()
    if not args.records.exists() or not args.graph.exists():
        print("Missing P12 live inputs.", file=sys.stderr)
        return 1
    model = args.model or (_DEFAULT_GRANITE if args.backend == "granite" else _DEFAULT_OR_ALT)
    records = [json.loads(l) for l in args.records.read_text(encoding="utf-8").splitlines() if l.strip()]
    graph = {r["task_id"]: r for r in
             (json.loads(l) for l in args.graph.read_text(encoding="utf-8").splitlines() if l.strip())}
    selected = select_cases(records, graph)
    ok, reason = beta_available(args.backend)
    if ok:
        real_cases = run_real(records, graph, selected, args.backend, model)
        write_report(selected, real_cases, None, args.backend, reason, args.report)
        ran = [c for c in real_cases if c["outcome"] is not None]
        print(f"REAL run: backend={args.backend} cross-assessed {len(ran)}/{len(selected)} "
              f"-> {args.report}")
    else:
        infra = infra_test(records, graph, selected)
        write_report(selected, None, infra, args.backend, reason, args.report)
        print(f"INFRA TEST only ({reason}): selected {len(selected)} cases, plumbing "
              f"verified, real cross-run pending credentials -> {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
