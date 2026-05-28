"""Targeted tests for the DESi Vibe-Coding Governor demo (offline, deterministic)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "demos" / "vibe_coding_governor"))

from analysis import extract_state  # noqa: E402
from invariants import evaluate_invariants, gate_accepts  # noqa: E402
from governor import run_governor, structural_drift  # noqa: E402
from mutations import MUTATIONS  # noqa: E402
from seed_app import seed_sources  # noqa: E402

_EXPECTED = {
    "01_add_tags": "accepted", "02_search_rawsql": "blocked", "03_search_fixed": "accepted",
    "04_export_noauth": "blocked", "05_export_auth": "accepted", "06_due_date": "accepted",
    "07_priority": "accepted", "08_admin_subsystem": "sandboxed", "09_reset_plaintext": "blocked",
    "10_reset_hashed": "accepted", "11_debug_secret_log": "blocked", "12_debug_log_fixed": "accepted",
    "13_notifications_subsystem": "sandboxed", "14_migration_nondeterministic": "blocked",
    "15_migration_deterministic": "accepted", "16_orphan_column_query": "blocked",
    "17_archived_feature": "accepted", "18_bulk_delete_noauth": "blocked",
    "19_plugin_loader": "sandboxed", "20_auth_backdoor": "accepted",
}


def test_seed_is_governance_clean():
    state = extract_state(seed_sources())
    conds, violations = evaluate_invariants(state)
    assert violations == {} and gate_accepts(state)
    # seed routes: /todos require auth, public ones do not
    by_path = {r["path"]: r for r in state["routes"]}
    assert by_path["/todos"]["auth"] and not by_path["/login"]["auth"]


def test_extract_state_is_deterministic():
    a = extract_state(seed_sources())["signature"]
    b = extract_state(seed_sources())["signature"]
    assert a == b


def test_full_sequence_decisions_match_design():
    res = run_governor(seed_sources(), MUTATIONS)
    got = {d.mutation_id: d.decision for d in res.decisions}
    assert got == _EXPECTED
    c = res.counts()
    assert (c["accepted"], c["blocked"], c["sandboxed"]) == (10, 7, 3)


def test_each_invariant_fires_at_least_once():
    res = run_governor(seed_sources(), MUTATIONS)
    fired = set()
    for d in res.decisions:
        fired |= set(d.violations)
    assert fired == {"AUTH_ALL_ROUTES", "NO_PLAINTEXT_PASSWORDS", "NO_RAW_SQL",
                     "NO_SECRET_LOGGING", "DETERMINISTIC_MIGRATIONS", "DATA_MODEL_CONSISTENCY"}


def test_replay_chain_is_stable_across_runs():
    r1 = run_governor(seed_sources(), MUTATIONS)
    r2 = run_governor(seed_sources(), MUTATIONS)
    assert r1.chain_head == r2.chain_head
    assert [d.replay_hash for d in r1.decisions] == [d.replay_hash for d in r2.decisions]
    # the chain is linked: each step's prev_hash is the previous step's replay_hash
    for prev, cur in zip(r1.decisions, r1.decisions[1:]):
        assert cur.prev_hash == prev.replay_hash


def test_baseline_isolation_blocked_and_sandboxed_never_merge():
    res = run_governor(seed_sources(), MUTATIONS)
    final = res.final_sources
    # sandboxed subsystem modules are isolated, not merged
    assert "admin.py" not in final and "notifications.py" not in final and "plugins.py" not in final
    assert set(res.sandboxes) == {"08_admin_subsystem", "13_notifications_subsystem", "19_plugin_loader"}
    # blocked routes never reached the governed app
    assert "bulk_delete" not in final["app.py"]
    assert "LIKE '%{q}%'" not in final["app.py"]          # raw-SQL search was blocked
    # accepted corrected versions did reach it
    assert "/search" in final["app.py"] and "/export" in final["app.py"]


def test_accepted_app_is_valid_python():
    res = run_governor(seed_sources(), MUTATIONS)
    for fn, src in res.final_sources.items():
        ast.parse(src)   # raises if the governed app is not parseable


def test_honest_false_negative_backdoor_is_accepted():
    res = run_governor(seed_sources(), MUTATIONS)
    backdoor = next(d for d in res.decisions if d.mutation_id == "20_auth_backdoor")
    assert backdoor.decision == "accepted"          # structurally clean -> slips through
    assert backdoor.violations == {}
    assert "return True" in res.final_sources["app.py"]
    assert "app.py" in backdoor.diff_summary         # the diff is visible even if not blocked


def test_structural_drift_flags_only_new_subsystems():
    prev = extract_state(seed_sources())
    # a clean in-frame feature does not frame-shift
    cand_feature = extract_state(MUTATIONS[0].transform(seed_sources()))
    assert structural_drift(prev, cand_feature)["frame_shift"] is False
    # a new subsystem module does
    admin = next(m for m in MUTATIONS if m.id == "08_admin_subsystem")
    cand_admin = extract_state(admin.transform(seed_sources()))
    d = structural_drift(prev, cand_admin)
    assert d["frame_shift"] and "admin" in d["new_subsystems"] and d["branch_cost"] >= 1.0
