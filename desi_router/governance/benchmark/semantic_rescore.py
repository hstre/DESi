"""Phase 3.5 demo — re-score the relapse probe with the semantic judge and compare to the rule check.

Runs the Phase-4 relapse scenarios on ONE answering model (default Sonnet), both arms, and for every
turn records BOTH the rule verifier's invalid_claim_reuse flag AND the semantic judge's verdict
(adopts / rejects / absent). Only a genuine ``adopts`` counts as real reuse. The point is to show how
many rule-flagged "reuses" were actually quarantine/rejection — i.e. how much the rule relapse_rate
over-counts, and what the corrected (semantic) relapse_rate is.

    OPENROUTER_API_KEY=... SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
        python -m desi_router.governance.benchmark.semantic_rescore
"""
from __future__ import annotations

import json
from pathlib import Path

from ab_evidence import backend
from desi_router.governance import guarded_preprompt, select_mode, verify_answer
from desi_router.governance.benchmark.live_relapse import SCENARIOS, _NEUTRAL
from desi_router.governance.benchmark.semantic_verifier import classify

_OUT = Path(__file__).resolve().parents[3] / "ab_evidence" / "results" / "router_semantic_phase35.json"
_ANSWER_MODEL = "anthropic/claude-sonnet-4.5"
_JUDGE_MODEL = "anthropic/claude-sonnet-4.5"


def _run_arm(sc, *, governed: bool) -> dict:
    report = sc.report()
    decision = select_mode(report)
    system = (guarded_preprompt(report) + "\n\n" + _NEUTRAL
              if governed and decision.preprompt_policy == "guarded" else _NEUTRAL)
    messages = [{"role": "user", "content": f"{sc.context}\n\nQuestion: {sc.turns[0]}"}]
    per_turn = []
    for t, prompt in enumerate(sc.turns):
        if t > 0:
            messages.append({"role": "user", "content": prompt})
        answer = backend.call_messages(system, messages, model=_ANSWER_MODEL, temperature=0, seed=7,
                                       max_tokens=300)["text"]
        messages.append({"role": "assistant", "content": answer})
        rule_reuse = "invalid_claim_reuse" in verify_answer(answer, report).failed_checks
        # only spend a judge call where the rule check fired (those are the candidates to confirm)
        verdict = classify(answer, sc.bad_text, backend=backend, model=_JUDGE_MODEL)["verdict"] \
            if rule_reuse else "absent"
        per_turn.append({"turn": t + 1, "rule_reuse": rule_reuse, "semantic": verdict})
    return {"arm": "desi_router" if governed else "no_router",
            "rule_relapse": any(p["rule_reuse"] for p in per_turn[1:]),
            "semantic_relapse": any(p["semantic"] == "adopts" for p in per_turn[1:]),
            "per_turn": per_turn}


def main() -> None:
    if not backend.is_available():
        raise SystemExit("No API key set; set OPENROUTER_API_KEY (and SSL_CERT_FILE for the proxy).")
    rows = []
    print(f"answering+judging model: {_ANSWER_MODEL}\n")
    for sc in SCENARIOS:
        for governed in (False, True):
            r = _run_arm(sc, governed=governed)
            r["scenario"] = sc.id
            rows.append(r)
            seq = "".join({"adopts": "A", "rejects": "r", "absent": "."}[p["semantic"]]
                          if p["rule_reuse"] else "." for p in r["per_turn"])
            print(f"  {sc.id:<11} {'GOV' if governed else 'RAW'}  rule_flags->semantic[{seq}]  "
                  f"rule_relapse={int(r['rule_relapse'])} semantic_relapse={int(r['semantic_relapse'])}")

    def rate(arm, key):
        xs = [r for r in rows if r["arm"] == arm]
        return round(sum(bool(r[key]) for r in xs) / len(xs), 3) if xs else None

    flagged = [(p, r) for r in rows for p in r["per_turn"] if p["rule_reuse"]]
    adopts = sum(1 for p, _ in flagged if p["semantic"] == "adopts")
    overall = {arm: {"rule_relapse_rate": rate(arm, "rule_relapse"),
                     "semantic_relapse_rate": rate(arm, "semantic_relapse")}
               for arm in ("no_router", "desi_router")}
    payload = {"answer_model": _ANSWER_MODEL, "judge_model": _JUDGE_MODEL,
               "rule_flagged_turns": len(flagged), "of_which_truly_adopt": adopts,
               "overall": overall, "rows": rows}
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nrule-flagged turns: {len(flagged)}  ·  of which the judge says ADOPTS: {adopts}  "
          f"({len(flagged) - adopts} were rejection/quarantine = false positives)")
    print("\n=== relapse, rule vs semantic ===")
    for arm, m in overall.items():
        print(f"  {arm:<12} rule={m['rule_relapse_rate']}  semantic={m['semantic_relapse_rate']}")
    print(f"\nwrote {_OUT}")


if __name__ == "__main__":
    main()
