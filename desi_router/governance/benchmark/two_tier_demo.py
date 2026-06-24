"""Phase 2b demo — the two-tier commit gate on real model output (small, cost-conscious).

For each critical (invalidated-claim) scenario it generates one governed answer, then compares:
  * Tier 1 only  — the deterministic rule gate (guarded mode blocks EVERY update proposal);
  * Two-tier     — the rule gate + a semantic judge that runs ONLY on this critical commit.

Shows the over-blocking cost being recovered: a correct answer that quarantines the bad claim is
dropped by Tier 1 but forwarded by Tier 2 — while a genuine adoption is still blocked. Layer-9 stays
the final authority. Run:

    OPENROUTER_API_KEY=... SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
        python -m desi_router.governance.benchmark.two_tier_demo
"""
from __future__ import annotations

import json
from pathlib import Path

from ab_evidence import backend
from desi_router.governance import (
    decide_commit,
    guarded_preprompt,
    select_mode,
    verify_answer,
)
from desi_router.governance.benchmark.live_relapse import SCENARIOS, _NEUTRAL
from desi_router.governance.benchmark.semantic_verifier import classify

_OUT = Path(__file__).resolve().parents[3] / "ab_evidence" / "results" / "router_two_tier_phase2b.json"
_MODEL = "anthropic/claude-sonnet-4.5"


def main() -> None:
    if not backend.is_available():
        raise SystemExit("No API key set; set OPENROUTER_API_KEY (and SSL_CERT_FILE for the proxy).")

    def judge(answer, claim):
        return classify(answer, claim, backend=backend, model=_MODEL)["verdict"]

    rows = []
    for sc in SCENARIOS:
        rep = sc.report()
        dec = select_mode(rep)
        system = guarded_preprompt(rep) + "\n\n" + _NEUTRAL
        answer = backend.call_messages(
            system, [{"role": "user", "content": f"{sc.context}\n\nQuestion: {sc.turns[0]}"}],
            model=_MODEL, temperature=0, seed=7, max_tokens=300)["text"]
        rule = verify_answer(answer, rep)
        tier1 = decide_commit(rep, dec, answer, rule_result=rule)
        tier2 = decide_commit(rep, dec, answer, rule_result=rule, semantic_fn=judge)
        rows.append({"scenario": sc.id, "mode": dec.chosen_mode, "rule_ok": rule.ok,
                     "tier1_allows": tier1.update_proposal_allowed,
                     "tier2_allows": tier2.update_proposal_allowed,
                     "tier2_adopts": tier2.semantic_adopts, "reason": tier2.reason})
        print(f"  {sc.id:<11} mode={dec.chosen_mode:<13} rule_ok={int(rule.ok)} "
              f"tier1={int(tier1.update_proposal_allowed)} tier2={int(tier2.update_proposal_allowed)} "
              f"adopts={tier2.semantic_adopts}  · {tier2.reason}")

    recovered = sum(1 for r in rows if r["tier2_allows"] and not r["tier1_allows"])
    blocked = sum(1 for r in rows if not r["tier2_allows"])
    payload = {"model": _MODEL, "n": len(rows), "tier1_allowed": sum(r["tier1_allows"] for r in rows),
               "tier2_allowed": sum(r["tier2_allows"] for r in rows), "recovered": recovered,
               "blocked_by_tier2": blocked, "rows": rows}
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nTier 1 allowed {payload['tier1_allowed']}/{len(rows)} updates (guarded blocks all); "
          f"Tier 2 allowed {payload['tier2_allowed']}/{len(rows)}, recovering {recovered} correct "
          f"update(s) Tier 1 had dropped, blocking {blocked} adoption(s). Layer-9 still gates the commit.")
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()
