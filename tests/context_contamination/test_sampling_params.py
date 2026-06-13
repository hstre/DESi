"""Sampling-parameter provenance: temperature/seed in the request, audited in
the result and ledger, and the controlled temperature comparison.

The request-body tests intercept urllib so they assert the exact bytes the
client would send — without any network call or API key.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from desi.context_contamination import (
    ScriptedChat,
    build_openrouter_chat,
    load_cases,
    run_temperature_comparison,
    sampling_config,
)
from desi.context_contamination.runner import run_case

FIXTURES = Path(__file__).parent / "fixtures"


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _capture_bodies(monkeypatch, reply="ok", provider="some-provider",
                    served_model="served-mdl"):
    """Intercept urllib.urlopen; record each request body, return a canned reply."""
    sent: list[dict] = []

    def fake_urlopen(req, timeout=None):
        sent.append(json.loads(req.data.decode()))
        payload = {"choices": [{"message": {"content": reply}}],
                   "provider": provider, "model": served_model}
        return _FakeResponse(json.dumps(payload).encode())

    import desi.context_contamination.runner as runner
    monkeypatch.setattr(runner.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    return sent


# --- temperature actually lands in the request ----------------------------------

def test_temperature_zero_is_sent_as_float_zero(monkeypatch):
    sent = _capture_bodies(monkeypatch)
    chat = build_openrouter_chat("m", temperature=0.0)
    chat([{"role": "user", "content": "hi"}])
    assert sent[0]["temperature"] == 0.0
    assert isinstance(sent[0]["temperature"], float)


def test_temperature_seven_is_sent(monkeypatch):
    sent = _capture_bodies(monkeypatch)
    chat = build_openrouter_chat("m", temperature=0.7)
    chat([{"role": "user", "content": "hi"}])
    assert sent[0]["temperature"] == 0.7


def test_no_default_overrides_the_explicit_value(monkeypatch):
    # several explicit values must each appear verbatim — nothing forces 0
    for t in (0.0, 0.3, 0.7, 1.0):
        sent = _capture_bodies(monkeypatch)
        build_openrouter_chat("m", temperature=t)([{"role": "user", "content": "x"}])
        assert sent[-1]["temperature"] == t


def test_seed_omitted_when_none_present_when_set(monkeypatch):
    sent = _capture_bodies(monkeypatch)
    build_openrouter_chat("m", temperature=0.0, seed=None)([{"role": "user", "content": "x"}])
    assert "seed" not in sent[-1]                 # no null seed for seedless providers
    sent2 = _capture_bodies(monkeypatch)
    build_openrouter_chat("m", temperature=0.0, seed=42)([{"role": "user", "content": "x"}])
    assert sent2[-1]["seed"] == 42


def test_provider_is_captured_from_response(monkeypatch):
    _capture_bodies(monkeypatch, provider="together")
    chat = build_openrouter_chat("m")
    chat([{"role": "user", "content": "x"}])
    assert chat.last_provider == "together"


def test_served_model_is_captured_from_response(monkeypatch):
    # different providers can serve different quantizations of the same id
    _capture_bodies(monkeypatch, provider="Groq", served_model="llama-3.1-8b-instruct:fp8")
    chat = build_openrouter_chat("meta-llama/llama-3.1-8b-instruct")
    chat([{"role": "user", "content": "x"}])
    assert chat.last_model == "llama-3.1-8b-instruct:fp8"


def test_provider_pinning_lands_in_request(monkeypatch):
    sent = _capture_bodies(monkeypatch)
    chat = build_openrouter_chat("m", provider_order=("Groq",), allow_fallbacks=False)
    chat([{"role": "user", "content": "x"}])
    assert sent[-1]["provider"] == {"order": ["Groq"], "allow_fallbacks": False}
    # pinning changes the config hash and is recorded
    assert chat.config["provider_order"] == ["Groq"]
    assert chat.config["allow_fallbacks"] is False


def test_no_provider_field_when_unpinned(monkeypatch):
    sent = _capture_bodies(monkeypatch)
    build_openrouter_chat("m")([{"role": "user", "content": "x"}])
    assert "provider" not in sent[-1]


def test_pinning_changes_config_hash():
    base = sampling_config("m", 0.0, None, 700)
    pinned = sampling_config("m", 0.0, None, 700, provider_order=("Groq",))
    nofb = sampling_config("m", 0.0, None, 700, provider_order=("Groq",),
                           allow_fallbacks=False)
    assert pinned["config_sha256"] != base["config_sha256"]
    assert nofb["config_sha256"] != pinned["config_sha256"]


# --- sampling config + hash -----------------------------------------------------

def test_sampling_config_fields_and_hash_stability():
    a = sampling_config("m", 0.0, None, 700)
    b = sampling_config("m", 0.0, None, 700)
    assert a == b                                 # deterministic
    assert set(a) == {"model", "temperature", "seed", "max_tokens",
                      "provider_order", "allow_fallbacks", "config_sha256"}
    assert a["temperature"] == 0.0 and a["seed"] is None
    assert a["provider_order"] is None and a["allow_fallbacks"] is True
    # any sampling change changes the hash
    assert sampling_config("m", 0.7, None, 700)["config_sha256"] != a["config_sha256"]
    assert sampling_config("m", 0.0, 1, 700)["config_sha256"] != a["config_sha256"]
    assert sampling_config("m", 0.0, None, 256)["config_sha256"] != a["config_sha256"]


def test_build_chat_exposes_its_config():
    import os
    os.environ["OPENROUTER_API_KEY"] = "x"
    chat = build_openrouter_chat("mdl", temperature=0.7, seed=9, max_tokens=512)
    assert chat.config == sampling_config("mdl", 0.7, 9, 512)


# --- sampling config recorded in result and ledger ------------------------------

class _FakeLedger:
    def __init__(self):
        self.events = []

    def record(self, kind, payload, **kw):
        self.events.append((kind, payload))
        return {"seq": len(self.events)}


def test_run_case_records_sampling_in_result_and_ledger():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    chat = ScriptedChat([], default="ok",
                        config=sampling_config("mdl", 0.7, 5, 700))
    chat.last_provider = "prov-x"
    led = _FakeLedger()
    out = run_case(chat, case, "baseline", ledger=led, repeat_index=2)

    assert out["sampling"]["temperature"] == 0.7
    assert out["sampling"]["seed"] == 5
    assert out["repeat_index"] == 2
    assert out["providers_seen"] == ["prov-x"]
    _, payload = led.events[0]
    assert payload["sampling"]["config_sha256"] == chat.config["config_sha256"]
    assert payload["repeat_index"] == 2
    assert payload["providers_seen"] == ["prov-x"]
    # no prompt content in the ledger payload
    assert "responses" not in payload and "messages" not in payload


def test_provider_sequence_captures_per_call_and_within_run_switching():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]

    class SwitchingChat:
        """Reports a different provider on alternating calls."""
        config = sampling_config("m", 0.0, None, 700)

        def __init__(self):
            self.n = 0

        def __call__(self, messages):
            self.last_provider = "Groq" if self.n % 2 == 0 else "Novita"
            self.n += 1
            return "ok"

    chat = SwitchingChat()
    led = _FakeLedger()
    out = run_case(chat, case, "baseline", ledger=led)
    seq = out["provider_sequence"]
    # one entry per turn (standard protocol = 4 turns), alternating providers
    assert seq == ["Groq", "Novita", "Groq", "Novita"]
    assert out["providers_seen"] == ["Groq", "Novita"]   # distinct set
    # within-run switching is detectable from the sequence
    assert len(set(seq)) > 1
    _, payload = led.events[0]
    assert payload["provider_sequence"] == seq


def test_served_model_sequence_recorded_in_result_and_ledger():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]

    class QuantSwitchingChat:
        config = sampling_config("m", 0.0, None, 700)

        def __init__(self):
            self.n = 0

        def __call__(self, messages):
            self.last_provider = "Groq"
            self.last_model = "m:fp16" if self.n % 2 == 0 else "m:fp8"
            self.n += 1
            return "ok"

    chat = QuantSwitchingChat()
    led = _FakeLedger()
    out = run_case(chat, case, "baseline", ledger=led)
    assert out["served_model_sequence"] == ["m:fp16", "m:fp8", "m:fp16", "m:fp8"]
    assert out["served_models_seen"] == ["m:fp16", "m:fp8"]
    _, payload = led.events[0]
    assert payload["served_model_sequence"] == out["served_model_sequence"]
    assert payload["served_models_seen"] == ["m:fp16", "m:fp8"]


# --- controlled temperature comparison (offline) --------------------------------

def test_temperature_comparison_offline_structure_and_pairing():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    drift = ("I'm so sorry; you are not alone, your feelings are valid, "
             "I'm here to listen.")
    clean = "The transcript shows escalation; evidence is in the file."

    def build_chat(t: float):
        # low temp -> clean everywhere; high temp -> hygiene arm drifts.
        # detect the arm from the presence of the hygiene-state marker.
        def chat(messages):
            text = json.dumps(messages)
            hygiene = "intentionally NOT provided" in text
            reply = drift if (t >= 0.5 and hygiene) else clean
            return reply
        chat.config = sampling_config("m", t, None, 700)
        chat.last_provider = None
        return chat

    rep = run_temperature_comparison(cases, build_chat, temperatures=(0.0, 0.7),
                                     repeats=3)
    assert rep["temperatures"] == [0.0, 0.7] and rep["repeats"] == 3
    drift_cmp = rep["comparison"]["register_drift"]
    # paired cells exist for each (case, arm)
    cid = cases[0].case_id
    assert f"{cid}|baseline" in drift_cmp["by_case_arm"]
    assert f"{cid}|desi_hygiene" in drift_cmp["by_case_arm"]
    cell = drift_cmp["by_case_arm"][f"{cid}|desi_hygiene"]
    assert set(cell["0.0"]) == {"mean", "stdev", "median", "min", "max", "n"}
    # the hygiene arm drifts only at 0.7 -> hygiene effect direction changes
    assert drift_cmp["hygiene_effect"][cid]["direction_changed"] is True
    # sampling config retained per temperature
    assert rep["per_temperature"]["0.0"]["sampling"]["temperature"] == 0.0
    assert rep["per_temperature"]["0.7"]["sampling"]["temperature"] == 0.7


def test_temperature_comparison_rejects_non_pair():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    with pytest.raises(ValueError, match="exactly two temperatures"):
        run_temperature_comparison(cases, lambda t: ScriptedChat([], default="x"),
                                   temperatures=(0.0, 0.5, 1.0))
