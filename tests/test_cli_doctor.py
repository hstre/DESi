"""Tests for `desi doctor` / `desi config` and the offline example.

All must work with NO API key and must never print a key value.
"""
from __future__ import annotations

import desi.governance_cli as cli


# --- doctor / config run offline ----------------
def test_doctor_runs_without_api_key(monkeypatch, capsys) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    rc = cli.main(["doctor"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "DESi Doctor" in out
    assert "Offline mode: ON" in out
    assert "ready for offline use" in out


def test_config_runs_and_hides_keys(monkeypatch, capsys) -> None:
    fake = "sk-or-v1-DOCTORTESTKEY999"
    monkeypatch.setenv("OPENROUTER_API_KEY", fake)
    rc = cli.main(["config"])
    out = capsys.readouterr().out
    assert rc == 0
    assert fake not in out          # key value never printed
    assert "api_key_set" in out     # only presence is shown
    assert "offline_mode" in out


def test_doctor_reports_key_set_without_printing_it(
    monkeypatch, capsys,
) -> None:
    fake = "sk-or-v1-DOCTORTESTKEY888"
    monkeypatch.setenv("OPENROUTER_API_KEY", fake)
    cli.main(["doctor"])
    out = capsys.readouterr().out
    assert fake not in out


def test_all_six_subcommands_registered() -> None:
    assert set(cli._DISPATCH) == {
        "replay", "audit", "benchmark", "review", "config", "doctor",
    }


# --- hello_desi example runs offline ------------
def test_hello_desi_runs_offline(monkeypatch, capsys) -> None:
    import pathlib

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # examples/ is not a package; exec the file directly.
    root = pathlib.Path(__file__).resolve().parents[1]
    src = (root / "examples" / "hello_desi.py").read_text(
        encoding="utf-8")
    ns: dict = {}
    exec(compile(src, "hello_desi.py", "exec"), ns)
    ns["main"]()
    out = capsys.readouterr().out
    assert "offline" in out.lower()
    assert "identical  : True" in out
