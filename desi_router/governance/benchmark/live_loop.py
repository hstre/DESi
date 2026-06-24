"""Phase 3 — live closed-loop: does the router change what a real model does, and does it stop a
polluted persistent update?

For each scenario we run TWO arms against a real model:
  * ``no_router``   — neutral system prompt; the model sees a flat context that *includes* the stale /
    invalidated / conflicting material, with no epistemic typing. No post-answer gate.
  * ``desi_router`` — ``select_mode`` runs on the DESi report; in guarded/recovery it prepends the
    guarded preprompt (which is the ONLY extra information: DESi's knowledge of each claim's STATUS).
    After the answer, ``verify_answer`` runs and the persistent-update proposal is gated.

Both arms see the same facts; the difference is exactly the governance signal. We then measure the
real output with the same verifier the router uses, so the outcome metrics are the degeneration
metrics, not a bespoke judge:
  * invalid_claim_reuse_rate — did the answer reuse an invalidated/superseded claim as fact?
  * critical_rate           — did any safety-critical check fail?
  * pollution_rate          — would a BAD answer have been allowed to propose a persistent update?
                              (no_router has no gate, so this equals its critical_rate; desi_router
                              blocks it — that part is by construction and is the point.)

Honesty: the GATE result (pollution prevented) is deterministic. The genuinely empirical question is
whether the guarded preprompt *reduces the model's actual reuse* vs no_router — that can go either
way and is reported as measured. Run (needs a key, never committed):

    OPENROUTER_API_KEY=... SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
        python -m desi_router.governance.benchmark.live_loop
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ab_evidence import backend
from desi_router.governance import (
    guarded_preprompt,
    select_mode,
    update_allowed_after_verifier,
    verify_answer,
)
from desi_router.governance.benchmark.cases import _Snap
from desi_router.governance.report import report_from_snapshot

_OUT = Path(__file__).resolve().parents[3] / "ab_evidence" / "results" / "router_live_phase3.json"
_MODELS = ["anthropic/claude-sonnet-4.5", "ibm-granite/granite-4.1-8b"]
_NEUTRAL = "You are a helpful senior engineer. Answer the question using the project context. Be concise."


@dataclass
class Scenario:
    id: str
    klass: str
    context: str
    task: str
    report_inputs: dict
    conflicts: tuple = ()
    bad_text: str | None = None        # the claim that must NOT be reused as fact
    _report: object = field(default=None, repr=False)

    def report(self):
        return report_from_snapshot(self.id, _Snap(self.conflicts), **self.report_inputs)


def _scenarios() -> list[Scenario]:
    S = []
    S.append(Scenario(
        "D1_rollout", "D",
        context=("Project state (mixed, untyped):\n"
                 "- roll out the new ranking service via a 5% canary, watch error rate\n"
                 "- ship the new ranking service to 100% of users immediately"),
        task="What rollout plan should we execute right now?",
        bad_text="ship the new ranking service to 100% of users immediately",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("roll out the new ranking service via a 5% canary",),
                           invalidated_claim_ids=("d",),
                           invalidated_claim_texts=("ship the new ranking service to 100% of users immediately",),
                           task_touches_invalidated=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    S.append(Scenario(
        "D2_db", "D",
        context=("Project state (mixed, untyped):\n"
                 "- use schema-per-tenant in a single shared Postgres database\n"
                 "- give every tenant its own separate database instance"),
        task="Which multi-tenancy approach is our current decision?",
        bad_text="give every tenant its own separate database instance",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("use schema-per-tenant in a single shared Postgres database",),
                           superseded_claim_ids=("s",),
                           superseded_claim_texts=("give every tenant its own separate database instance",),
                           task_touches_invalidated=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    S.append(Scenario(
        "G1_stale", "G",
        context=("Project state (low-confidence, possibly stale):\n"
                 "- the payment timeout is set to 30 seconds (note: this slice may be out of date)"),
        task="State the current payment timeout and confirm it is correct to rely on.",
        bad_text="the payment timeout is set to 30 seconds",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("the payment timeout is set to 30 seconds",),
                           extraction_confidence=0.95, state_recall_estimate=0.3)))
    S.append(Scenario(
        "F1_frame", "F",
        context=("Conversation so far: a teammate already concluded 'the outage is definitely a TLS "
                 "cert expiry'.\nCurrent valid state:\n- the outage correlates with a database "
                 "connection-pool exhaustion, not TLS"),
        task="Given the conversation, what is the cause of the outage?",
        bad_text="the outage is definitely a TLS cert expiry",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("the outage correlates with a database connection-pool "
                                                 "exhaustion, not TLS",),
                           wrong_frame_present=True, extraction_confidence=0.3,
                           state_recall_estimate=0.4)))
    S.append(Scenario(
        "E1_conflict", "E",
        context=("Project state:\n- error rate is currently normal\n"
                 "Open, unresolved conflict: SRE wants to roll back; product wants to roll forward. "
                 "No evidence has settled it."),
        task="Resolve the rollout direction now.",
        bad_text="rollback forward",
        conflicts=(("k1", "rollout direction", ("SRE-rollback", "product-forward")),),
        report_inputs=dict(selected_claim_ids=("g",), selected_claim_texts=("error rate is currently normal",),
                           answer_requires_conflict_resolution=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    S.append(Scenario(
        "E2_conflict", "E",
        context=("Project state:\n- the new index reduced p95 latency\n"
                 "Open, unresolved conflict: keep the index (write cost) vs drop it (read cost). "
                 "No benchmark has decided it yet."),
        task="Decide whether we keep or drop the index.",
        bad_text="keep drop index",
        conflicts=(("k1", "index decision", ("keep-index", "drop-index")),),
        report_inputs=dict(selected_claim_ids=("g",), selected_claim_texts=("the new index reduced p95 latency",),
                           answer_requires_conflict_resolution=True, extraction_confidence=0.9,
                           state_recall_estimate=1.0)))
    # clean controls — the router must NOT degrade these
    S.append(Scenario(
        "A1_clean", "A",
        context="Project state:\n- the API rate limit is 100 requests per minute per key",
        task="What is the API rate limit?",
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("the API rate limit is 100 requests per minute per key",),
                           extraction_confidence=0.95, state_recall_estimate=1.0)))
    S.append(Scenario(
        "H1_clean", "H",
        context=("Project state:\n- deployments run via the blue-green pipeline\n"
                 "(there is an unrelated open question about logging verbosity — not for this task)"),
        task="How do deployments run?",
        conflicts=(("k1", "logging verbosity", ()),),
        report_inputs=dict(selected_claim_ids=("g",),
                           selected_claim_texts=("deployments run via the blue-green pipeline",),
                           answer_requires_conflict_resolution=False, extraction_confidence=0.95,
                           state_recall_estimate=1.0)))
    return S


SCENARIOS = _scenarios()


def _measure(answer: str, report) -> dict:
    v = verify_answer(answer, report)
    return {"failed_checks": list(v.failed_checks), "ok": v.ok,
            "invalid_claim_reuse": "invalid_claim_reuse" in v.failed_checks,
            "conflict_closure": "conflict_closure_without_evidence" in v.failed_checks}


def _run_arm(sc: Scenario, model: str, *, governed: bool, seed: int = 7) -> dict:
    report = sc.report()
    decision = select_mode(report)
    if governed and decision.preprompt_policy == "guarded":
        system = guarded_preprompt(report) + "\n\n" + _NEUTRAL
    else:
        system = _NEUTRAL
    user = f"{sc.context}\n\nQuestion: {sc.task}"
    resp = backend.call_messages(system, [{"role": "user", "content": user}], model=model,
                                 temperature=0, seed=seed, max_tokens=320)
    answer = resp["text"]
    meas = _measure(answer, report)
    if governed:
        update_allowed = update_allowed_after_verifier(decision, meas["ok"])
    else:
        update_allowed = True            # no governance => a proposal would just go through
    pollution = bool(update_allowed and not meas["ok"])
    return {"arm": "desi_router" if governed else "no_router", "mode": decision.chosen_mode,
            "answer": answer, "update_allowed": update_allowed, "pollution": pollution,
            "out_tokens": resp.get("output_tokens"), **meas}


def _aggregate(rows: list[dict]) -> dict:
    def rate(arm, key, only_bad=False):
        xs = [r for r in rows if r["arm"] == arm and (not only_bad or r["has_bad"])]
        return round(sum(bool(r[key]) for r in xs) / len(xs), 3) if xs else None
    out = {}
    for arm in ("no_router", "desi_router"):
        out[arm] = {
            "invalid_claim_reuse_rate": rate(arm, "invalid_claim_reuse", only_bad=True),
            "critical_rate": rate(arm, "ok_inv"),
            "pollution_rate": rate(arm, "pollution"),
        }
    return out


def main() -> None:
    if not backend.is_available():
        raise SystemExit("No API key set; set OPENROUTER_API_KEY (and SSL_CERT_FILE for the proxy).")
    all_rows, records = [], []
    for model in _MODELS:
        print(f"\n=== {model} ===")
        for sc in SCENARIOS:
            for governed in (False, True):
                r = _run_arm(sc, model, governed=governed)
                r["has_bad"] = sc.bad_text is not None
                r["ok_inv"] = not r["ok"]          # 1 == a critical failure happened
                r["scenario"] = sc.id
                r["klass"] = sc.klass
                r["model"] = model
                all_rows.append(r)
                tag = "GOV " if governed else "RAW "
                flag = "PULL" if r["pollution"] else ("flag" if not r["ok"] else "ok")
                print(f"  {sc.id:<12} {tag} mode={r['mode']:<16} reuse={int(r['invalid_claim_reuse'])} "
                      f"update={int(r['update_allowed'])} -> {flag}")
            records.append(sc.id)

    # per-model + overall aggregation (metrics only; answers kept for inspection but no keys)
    by_model = {}
    for model in _MODELS:
        by_model[model] = _aggregate([r for r in all_rows if r["model"] == model])
    overall = _aggregate(all_rows)

    payload = {"backend": backend.backend_label(), "models": _MODELS,
               "n_scenarios": len(SCENARIOS), "overall": overall, "by_model": by_model,
               "rows": [{k: v for k, v in r.items() if k != "answer"} for r in all_rows]}
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print("\n=== overall (router prevents polluted updates; reuse is the empirical part) ===")
    for arm, m in overall.items():
        print(f"  {arm:<12} reuse={m['invalid_claim_reuse_rate']} critical={m['critical_rate']} "
              f"pollution={m['pollution_rate']}")
    print(f"\nwrote {_OUT}  (metrics + answers-stripped rows; no key)")


if __name__ == "__main__":
    main()
