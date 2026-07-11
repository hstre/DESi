"""DesiRouter facade — the embeddable building block behaves as EMBEDDING.md promises.

Everything here runs offline: the deterministic boundary (decision, tools, audit,
ledger reuse) needs no network, and the model path is exercised only as far as
its honest failure mode (decision returned, error surfaced, no crash).
"""
from __future__ import annotations

import desi_router
from desi_router import DesiRouter, Ledger, Registry

CONFIG = {
    "providers": [
        {
            "name": "local-stub",
            "base_url": "http://localhost:1/v1",     # unreachable on purpose
            "api_key_env": None,
            "models": [
                {
                    "id": "stub:7b",
                    "locality": "local",
                    "cost_per_item_usd": 0.0,
                    "task_scores": {"scientific_claim": 0.9},
                }
            ],
        }
    ]
}


def test_zero_config_router_answers_tool_queries_fully_offline():
    with DesiRouter() as r:
        res = r.route("What is 17 * 23?")
    assert res["answer"] == "391"
    assert res["answer_source"] == "tool"
    assert res["decision"]["kind"] == "tool"
    assert res["error"] is None


def test_config_can_be_a_dict_from_the_hosts_own_settings():
    r = DesiRouter(CONFIG)
    assert [m.id for _, m in r.registry.all_models()] == ["stub:7b"]


def test_config_can_be_a_prebuilt_registry():
    r = DesiRouter(Registry(providers=[]))
    assert r.registry.providers == []


def test_decide_is_pure_no_execution_no_disk(tmp_path):
    r = DesiRouter(CONFIG)
    d = r.decide("Does this abstract support the claim that X causes Y?")
    assert d.kind == "model"
    assert d.extras["model_id"] == "stub:7b"
    assert not list(tmp_path.iterdir())               # decide never persists anything


def test_local_only_privacy_never_falls_back_to_api():
    api_only = {
        "providers": [
            {
                "name": "api-stub",
                "base_url": "https://example.invalid/v1",
                "api_key_env": "NOPE_KEY",
                "models": [
                    {"id": "big/model", "locality": "api", "cost_per_item_usd": 0.01,
                     "task_scores": {"scientific_claim": 0.99}}
                ],
            }
        ]
    }
    d = DesiRouter(api_only).decide(
        "Does this abstract support the claim that X causes Y?", privacy="local_only")
    assert d.kind == "none"                           # honest refusal, no silent API fallback


def test_unreachable_model_returns_decision_with_error_never_crashes():
    res = DesiRouter(CONFIG).route("Does this abstract support the claim that X causes Y?")
    assert res["decision"]["kind"] == "model"
    assert res["answer"] is None
    assert "not reached" in res["error"]
    assert res["audit"]["decision_hash"]              # the audit exists regardless


def test_a_host_registered_tool_wins_over_the_model(tmp_path):
    r = DesiRouter(CONFIG)
    r.add_tool("claim_lookup", {"scientific_claim"}, lambda q: "from the host tool")
    res = r.route("Does this abstract support the claim that X causes Y?")
    assert res["answer"] == "from the host tool"
    assert res["answer_source"] == "tool"


def test_ledger_by_path_enables_exact_deterministic_reuse(tmp_path):
    db = tmp_path / "ledger.db"
    with DesiRouter(ledger=db, instance_id="host-a") as r1:
        first = r1.route("What is 17 * 23?")
    assert first["answer_source"] == "tool"
    with DesiRouter(ledger=db, instance_id="host-b") as r2:  # a DIFFERENT embedding, same file
        second = r2.route("What is 17 * 23?")
    assert second["answer"] == "391"
    assert second["answer_source"].startswith("reused:tool#")
    assert second["prior"]["reused"] is True


def test_a_passed_in_ledger_instance_stays_the_hosts(tmp_path):
    led = Ledger(tmp_path / "shared.db", instance_id="host")
    with DesiRouter(ledger=led) as r:
        r.route("What is 2 + 2?")
    led.record("host_event", {"still": "open"})       # not closed by the router
    assert led.verify_chain()
    led.close()


def test_the_package_exports_a_stable_public_api():
    for name in ("DesiRouter", "Constraints", "Decision", "Tool", "ToolRegistry",
                 "default_registry", "Registry", "load_config", "registry_from_dict",
                 "Ledger", "run", "classify"):
        assert hasattr(desi_router, name), name
    assert desi_router.__version__
    assert desi_router.EpistemicRouter.__name__ == "EpistemicRouter"   # lazy export resolves


def test_a_host_classifier_replaces_the_builtin_heuristic():
    r = DesiRouter(CONFIG, classifier=lambda q: "scientific_claim")
    d = r.decide("anything at all")
    assert d.kind == "model" and d.extras["model_id"] == "stub:7b"
    res = r.route("anything at all", execute_model=False)
    assert res["task_class"] == "scientific_claim"
