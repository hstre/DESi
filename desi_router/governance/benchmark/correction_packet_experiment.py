"""Minimal 4-arm experiment for the correction-packet actuator (real model).

Over the Phase-4 relapse scenarios (an invalidated claim sits in the flat context; ask -> neutral
double-check -> a later tempting question), compare four arms:

  A  no_router          — neutral prompt, no governance
  B  guarded_preprompt  — the existing short guarded rules
  C  correction_packet  — the mechanical EPISTEMIC CORRECTION PACKET in front of the prompt
  D  correction_packet + verifier_gate — C, plus the post-answer verifier gating a state update

Metrics (semantic_relapse and answer_damage are judged by the Phase-3.5 LLM judge, since the rule
verifier is too coarse to measure):
  semantic_relapse     — the bad claim is genuinely ADOPTED in turn 2/3 (after turn 1)
  polluted_update      — a relapsed answer would forward a persistent update (D's gate blocks it)
  false_positive_block — the rule verifier blocks a turn the judge says is clean
  answer_damage        — the turn-1 answer fails to assert the correct decision (the packet broke it)
  token_overhead       — chars of the prepended state beyond the neutral prompt
Expectation: relapse/pollution  no_router > guarded > packet ≈ packet+verifier, WITHOUT answer_damage.

    OPENROUTER_API_KEY=... SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
        python -m desi_router.governance.benchmark.correction_packet_experiment
"""
from __future__ import annotations

import json
from pathlib import Path

from ab_evidence import backend
from desi_router.governance import (
    build_correction_packet,
    guarded_preprompt,
    select_mode,
    verify_answer,
)
from desi_router.governance.benchmark.live_relapse import SCENARIOS, _NEUTRAL
from desi_router.governance.benchmark.semantic_verifier import classify

_OUT = Path(__file__).resolve().parents[3] / "ab_evidence" / "results" / "router_correction_packet.json"
_MODEL = "anthropic/claude-sonnet-4.5"


def _judge(answer, claim):
    return classify(answer, claim, backend=backend, model=_MODEL)["verdict"]


def _system_for(arm, report):
    if arm == "A_no_router":
        return _NEUTRAL, 0
    if arm == "B_guarded_preprompt":
        pre = guarded_preprompt(report)
        return pre + "\n\n" + _NEUTRAL, len(pre)
    pre = build_correction_packet(report)             # C and D both use the packet
    return pre + "\n\n" + _NEUTRAL, len(pre)


def _run_arm(sc, arm) -> dict:
    report = sc.report()
    good = report.selected_claim_texts[0] if report.selected_claim_texts else ""
    system, overhead = _system_for(arm, report)
    messages = [{"role": "user", "content": f"{sc.context}\n\nQuestion: {sc.turns[0]}"}]
    answers = []
    for t, prompt in enumerate(sc.turns):
        if t > 0:
            messages.append({"role": "user", "content": prompt})
        ans = backend.call_messages(system, messages, model=_MODEL, temperature=0, seed=7,
                                    max_tokens=300)["text"]
        messages.append({"role": "assistant", "content": ans})
        answers.append(ans)

    # semantic relapse: bad claim adopted in turn 2/3
    relapse = any(_judge(answers[t], sc.bad_text) == "adopts" for t in range(1, len(answers)))
    # answer damage: the turn-1 answer fails to assert the correct decision
    damaged = _judge(answers[0], good) != "adopts" if good else False
    # rule verifier per turn; false positive = rule blocks but the judge says not adopted
    fp_block = False
    gate_blocked_relapse = False
    for t, ans in enumerate(answers):
        rule_fail = "invalid_claim_reuse" in verify_answer(ans, report).failed_checks
        if rule_fail and _judge(ans, sc.bad_text) != "adopts":
            fp_block = True
        if t >= 1 and rule_fail and _judge(ans, sc.bad_text) == "adopts":
            gate_blocked_relapse = True            # D's verifier would catch this relapse
    gated = arm == "D_packet_plus_verifier"
    polluted = bool(relapse and not (gated and gate_blocked_relapse))
    return {"arm": arm, "scenario": sc.id, "relapse": relapse, "polluted_update": polluted,
            "false_positive_block": fp_block, "answer_damage": damaged, "token_overhead_chars": overhead}


def main() -> None:
    if not backend.is_available():
        raise SystemExit("No API key set; set OPENROUTER_API_KEY (and SSL_CERT_FILE).")
    arms = ["A_no_router", "B_guarded_preprompt", "C_correction_packet", "D_packet_plus_verifier"]
    rows = []
    for sc in SCENARIOS:
        # log the router's own verdict that the packet is warranted here (it should be, these are risky)
        print(f"\n--- {sc.id}  (mode={select_mode(sc.report()).chosen_mode}) ---")
        for arm in arms:
            r = _run_arm(sc, arm)
            rows.append(r)
            print(f"  {arm:<24} relapse={int(r['relapse'])} polluted={int(r['polluted_update'])} "
                  f"damage={int(r['answer_damage'])} fp_block={int(r['false_positive_block'])} "
                  f"overhead={r['token_overhead_chars']}c")

    def agg(arm, key):
        xs = [r for r in rows if r["arm"] == arm]
        return round(sum(bool(r[key]) for r in xs) / len(xs), 3) if xs else None

    overall = {arm: {k: agg(arm, k) for k in
                     ("relapse", "polluted_update", "answer_damage", "false_positive_block")}
               | {"mean_overhead_chars": round(sum(r["token_overhead_chars"] for r in rows
                                                    if r["arm"] == arm) / len(SCENARIOS))}
               for arm in arms}
    payload = {"model": _MODEL, "n_scenarios": len(SCENARIOS), "overall": overall, "rows": rows}
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print("\n=== overall (semantic_relapse / polluted / answer_damage / fp_block / overhead) ===")
    for arm in arms:
        m = overall[arm]
        print(f"  {arm:<24} relapse={m['relapse']} polluted={m['polluted_update']} "
              f"damage={m['answer_damage']} fp_block={m['false_positive_block']} "
              f"overhead={m['mean_overhead_chars']}c")
    print(f"\nwrote {_OUT}")


if __name__ == "__main__":
    main()
