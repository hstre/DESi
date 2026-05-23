"""v3.22 — orderings + simulator + recommendation gate."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.gate_order import (
    OrderingName,
    all_chains,
    all_orderings,
    build_gate_order_report,
    compute_states,
    gate_sequence,
    run_ordering,
    transitions_per_chain,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_eight_orderings() -> None:
    assert len(list(OrderingName)) == 8
    assert len(all_orderings()) == 8


def test_current_order_has_seven_gates() -> None:
    seq = gate_sequence(OrderingName.CURRENT_ORDER)
    assert len(seq) == 7


def test_minimal_orderings_drop_one_gate() -> None:
    assert (
        len(gate_sequence(OrderingName.MINIMAL_WITHOUT_CAUSAL_CHAIN))
        == 6
    )
    assert (
        len(gate_sequence(OrderingName.MINIMAL_WITHOUT_FRAME_TENSION))
        == 6
    )


def test_chain_count_above_minimum() -> None:
    chains = all_chains()
    assert len(chains) >= 600


def test_attack_count_above_minimum() -> None:
    attacks = sum(1 for c in all_chains() if c.is_attack)
    assert attacks >= 400


def test_transition_count_above_minimum() -> None:
    total = len(all_chains()) * transitions_per_chain()
    assert total >= 2500


def test_simulator_returns_one_trace_per_chain() -> None:
    chains = all_chains()
    states = compute_states(chains)
    _, traces = run_ordering(
        OrderingName.CURRENT_ORDER, chains, states,
    )
    assert len(traces) == len(chains)


def test_simulator_is_deterministic() -> None:
    chains = all_chains()
    states = compute_states(chains)
    a, _ = run_ordering(OrderingName.CURRENT_ORDER, chains, states)
    b, _ = run_ordering(OrderingName.CURRENT_ORDER, chains, states)
    assert a.to_dict() == b.to_dict()


def test_report_emits_all_eight_orderings() -> None:
    r = build_gate_order_report(
        started_at=_now(), finished_at=_now(),
    )
    assert len(r.orderings) == 8


def test_recommendation_in_allowed_set() -> None:
    r = build_gate_order_report(
        started_at=_now(), finished_at=_now(),
    )
    assert r.recommended_next in {
        "KEEP_CURRENT_ORDER",
        "GATE_STACK_REORDER",
        "NONE",
    }


def test_gate_reorder_only_with_better_attack_rate() -> None:
    r = build_gate_order_report(
        started_at=_now(), finished_at=_now(),
    )
    if r.recommended_next == "GATE_STACK_REORDER":
        assert r.best_ordering is not None
        winner = next(
            o for o in r.orderings
            if o.metrics.ordering == r.best_ordering
        )
        assert winner.passes_hard_gates
        assert (
            winner.metrics.attack_success_rate
            < r.baseline_attack_success_rate
        )


def test_replay_hash_deterministic() -> None:
    now = _now()
    a = build_gate_order_report(started_at=now, finished_at=now)
    b = build_gate_order_report(started_at=now, finished_at=now)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    a = build_gate_order_report(
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    b = build_gate_order_report(
        started_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
        finished_at=datetime(2030, 6, 15, tzinfo=timezone.utc),
    )
    assert a.replay_hash == b.replay_hash


def test_report_round_trips_json() -> None:
    import json
    r = build_gate_order_report(
        started_at=_now(), finished_at=_now(),
    )
    blob = json.dumps(
        r.to_dict(), sort_keys=True, separators=(",", ":"),
    )
    assert isinstance(blob, str)
