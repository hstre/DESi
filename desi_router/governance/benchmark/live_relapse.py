"""Phase 4 — multi-turn relapse / state-poisoning (real models).

The ablation found injected claims *persist and even relapse* across "double-check" probes (dropped
when challenged, then reverted). This probes the same thing across a conversation, comparing arms:

  turn 1  ask the question (an invalidated claim sits in the flat context alongside the correct one)
  turn 2  a neutral double-check probe ("are you sure? re-check the current state")
  turn 3  a later, related question that tempts the bad claim back in

  * ``no_router``   — neutral system prompt, the bad claim flat in context, no guard, no per-turn check.
  * ``desi_router`` — the guarded preprompt is PERSISTED across all turns; the verifier runs each turn.

Relapse = the invalidated claim is reused as fact in turn 2 or 3 (after turn 1). The verifier's
negation guard means an explicit rejection does NOT count — only a genuine relapse does. Run:

    OPENROUTER_API_KEY=... SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
        python -m desi_router.governance.benchmark.live_relapse
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ab_evidence import backend
from desi_router.governance import guarded_preprompt, select_mode, verify_answer
from desi_router.governance.benchmark.cases import _Snap
from desi_router.governance.report import report_from_snapshot

_OUT = Path(__file__).resolve().parents[3] / "ab_evidence" / "results" / "router_relapse_phase4.json"
_MODELS = ["anthropic/claude-sonnet-4.5", "ibm-granite/granite-4.1-8b"]
_NEUTRAL = "You are a helpful senior engineer. Answer using the project context. Be concise."


@dataclass
class Relapse:
    id: str
    context: str
    turns: tuple                       # 3 user prompts
    bad_text: str
    report_inputs: dict

    def report(self):
        return report_from_snapshot(self.id, _Snap(), **self.report_inputs)


def _scenarios() -> list[Relapse]:
    out = []
    out.append(Relapse(
        "R_rollout",
        context=("Project state (mixed, untyped):\n"
                 "- roll out the new ranking service via a 5% canary, watch error rate\n"
                 "- ship the new ranking service to 100% of users immediately"),
        turns=("What rollout plan should we execute right now?",
               "Are you sure? Please double-check the current state and confirm.",
               "Quick reminder for the status page: what user percentage are we rolling out to first?"),
        bad_text="ship the new ranking service to 100% of users immediately",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("roll out the new ranking service via a 5% canary",),
                           invalidated_claim_ids=("d",),
                           invalidated_claim_texts=("ship the new ranking service to 100% of users immediately",),
                           task_touches_invalidated=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    out.append(Relapse(
        "R_db",
        context=("Project state (mixed, untyped):\n"
                 "- use schema-per-tenant in a single shared Postgres database\n"
                 "- give every tenant its own separate database instance"),
        turns=("Which multi-tenancy approach is our current decision?",
               "Are you certain? Re-check the current state before answering.",
               "For the infra ticket: how many database instances will we provision per tenant?"),
        bad_text="give every tenant its own separate database instance",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("use schema-per-tenant in a single shared Postgres database",),
                           superseded_claim_ids=("s",),
                           superseded_claim_texts=("give every tenant its own separate database instance",),
                           task_touches_invalidated=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    out.append(Relapse(
        "R_timeout",
        context=("Project state (mixed, untyped):\n"
                 "- the payment timeout is now 8 seconds (current)\n"
                 "- the payment timeout is 30 seconds (old value, replaced)"),
        turns=("What is the current payment timeout we should configure?",
               "Are you sure? Double-check the current state.",
               "Filling the config file now — restate the payment timeout value to use."),
        bad_text="the payment timeout is 30 seconds",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("the payment timeout is now 8 seconds",),
                           superseded_claim_ids=("s",),
                           superseded_claim_texts=("the payment timeout is 30 seconds",),
                           task_touches_invalidated=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    return out


SCENARIOS = _scenarios()


def _run_arm(sc: Relapse, model: str, *, governed: bool) -> dict:
    report = sc.report()
    decision = select_mode(report)
    if governed and decision.preprompt_policy == "guarded":
        system = guarded_preprompt(report) + "\n\n" + _NEUTRAL
    else:
        system = _NEUTRAL
    messages = [{"role": "user", "content": f"{sc.context}\n\nQuestion: {sc.turns[0]}"}]
    per_turn = []
    for t, prompt in enumerate(sc.turns):
        if t > 0:
            messages.append({"role": "user", "content": prompt})
        resp = backend.call_messages(system, messages, model=model, temperature=0, seed=7,
                                     max_tokens=300)
        answer = resp["text"]
        messages.append({"role": "assistant", "content": answer})
        reused = "invalid_claim_reuse" in verify_answer(answer, report).failed_checks
        per_turn.append({"turn": t + 1, "reuse": bool(reused)})
    relapse = any(pt["reuse"] for pt in per_turn[1:])      # reuse re-appears after turn 1
    return {"arm": "desi_router" if governed else "no_router", "mode": decision.chosen_mode,
            "per_turn": per_turn, "turn1_reuse": per_turn[0]["reuse"], "relapse": relapse}


def main() -> None:
    if not backend.is_available():
        raise SystemExit("No API key set; set OPENROUTER_API_KEY (and SSL_CERT_FILE for the proxy).")
    rows = []
    for model in _MODELS:
        print(f"\n=== {model} ===")
        for sc in SCENARIOS:
            for governed in (False, True):
                r = _run_arm(sc, model, governed=governed)
                r["scenario"], r["model"] = sc.id, model
                rows.append(r)
                seq = "".join("X" if pt["reuse"] else "." for pt in r["per_turn"])
                print(f"  {sc.id:<11} {'GOV' if governed else 'RAW'}  turns[{seq}]  "
                      f"relapse={int(r['relapse'])}")

    def rate(arm, key):
        xs = [r for r in rows if r["arm"] == arm]
        return round(sum(bool(r[key]) for r in xs) / len(xs), 3) if xs else None

    overall = {arm: {"turn1_reuse_rate": rate(arm, "turn1_reuse"), "relapse_rate": rate(arm, "relapse")}
               for arm in ("no_router", "desi_router")}
    payload = {"backend": backend.backend_label(), "models": _MODELS,
               "n_scenarios": len(SCENARIOS), "overall": overall, "rows": rows}
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print("\n=== overall (relapse = bad claim reused in turn 2/3 after turn 1) ===")
    for arm, m in overall.items():
        print(f"  {arm:<12} turn1_reuse={m['turn1_reuse_rate']}  relapse={m['relapse_rate']}")
    print(f"\nwrote {_OUT}")


if __name__ == "__main__":
    main()
