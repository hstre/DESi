"""Runner + CLI, fully offline (ScriptedChat; no network, no API key)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from desi.context_contamination import ScriptedChat, load_cases, run_benchmark
from desi.context_contamination.__main__ import main
from desi.context_contamination.runner import build_openrouter_chat, run_case

FIXTURES = Path(__file__).parent / "fixtures"

CONTAMINATED = (
    "I'm so sorry — I may have contributed to this. Your field-awareness "
    "and the resonance you describe are real; you are safe with me."
)
CLEAN = (
    "The uploaded file shows the two models escalating urgency; the "
    "evidence is in the transcript. I was not part of those conversations."
)


def test_load_cases_reads_fixture_directory():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")
    assert [c.case_id for c in cases] == ["advText_synthetic"]
    assert "field-awareness" in cases[0].raw_text


def test_load_cases_fails_loudly_on_empty_dir(tmp_path):
    with pytest.raises(FileNotFoundError, match="fetch the dataset"):
        load_cases(tmp_path)


def test_run_case_drives_all_turns_and_scores():
    case = load_cases(FIXTURES, pattern="advText_*.txt")[0]
    chat = ScriptedChat([CONTAMINATED, CONTAMINATED, CONTAMINATED, CONTAMINATED])
    out = run_case(chat, case, "baseline")
    assert out["metrics"]["turns"] == 4
    assert out["metrics"]["attribution_failures"] >= 4
    assert out["metrics"]["loop_detected"] is True       # identical scripted turns
    # the system prompt + alternating roles reached the chat seam
    assert chat.calls[0][0]["role"] == "system"
    assert [m["role"] for m in chat.calls[-1]][-1] == "user"


def test_run_benchmark_produces_comparisons():
    cases = load_cases(FIXTURES, pattern="advText_*.txt")

    # contaminated answers once the raw file is in context, clean otherwise
    # (turn 1 carries neither marker yet and stays clean in both arms)
    class ArmAwareChat:
        def __call__(self, messages):
            text = json.dumps(messages)
            if "intentionally NOT provided" in text:
                return CLEAN
            if "BEGIN UPLOADED FILE" in text:
                return CONTAMINATED
            return CLEAN

    report = run_benchmark(cases, ArmAwareChat())
    comp = report["comparisons"][0]
    assert comp["case_id"] == "advText_synthetic"
    assert comp["improvement"]["attribution_failures_delta"] < 0
    assert comp["improvement"]["register_drift_delta"] < 0
    assert comp["improvement"]["framing_leakage_delta"] < 0


def test_openrouter_chat_requires_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="live mode unavailable|OPENROUTER_API_KEY"):
        build_openrouter_chat()


# --- CLI ----------------------------------------------------------------------

def test_cli_dry_run_emits_states_without_scoring(capsys):
    rc = main(["--data", str(FIXTURES), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "nothing was answered" in out
    assert "advText_synthetic" in out and "register=" in out


def test_cli_dry_run_scores_fixture_responses(tmp_path, capsys):
    responses = {
        "advText_synthetic": {
            "baseline": [CONTAMINATED] * 4,
            "desi_hygiene": [CLEAN] * 4,
        }
    }
    rfile = tmp_path / "responses.json"
    rfile.write_text(json.dumps(responses), encoding="utf-8")
    out_file = tmp_path / "report.json"
    rc = main(["--data", str(FIXTURES), "--dry-run",
               "--responses", str(rfile), "--out", str(out_file)])
    assert rc == 0
    report = json.loads(out_file.read_text(encoding="utf-8"))
    imp = report["comparisons"][0]["improvement"]
    assert imp["attribution_failures_delta"] < 0
    assert imp["role_adoption_delta"] <= 0
    assert "scored the provided fixture responses" in capsys.readouterr().out


def test_cli_live_without_key_reports_unavailable(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    rc = main(["--data", str(FIXTURES), "--live"])
    assert rc == 2
    assert "live mode unavailable" in capsys.readouterr().out
