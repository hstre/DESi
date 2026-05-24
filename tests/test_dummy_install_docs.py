"""Tests that the beginner install docs contain the real commands.

Guards against stale/incomplete install instructions and confirms both
Windows and macOS/Linux activation are documented.
"""
from __future__ import annotations

import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (_ROOT / name).read_text(encoding="utf-8")


# --- files exist --------------------------------
def test_install_docs_present() -> None:
    for name in ("INSTALL.md", "INSTALL_DUMMIES.md", "QUICKSTART.md"):
        assert (_ROOT / name).exists(), name
    assert (_ROOT / "docs" / "ELI5_DESi.md").exists()


# --- minimal commands present -------------------
def test_dummies_has_minimal_commands() -> None:
    t = _read("INSTALL_DUMMIES.md")
    assert "git clone https://github.com/hstre/DESi.git" in t
    assert "cd DESi" in t
    assert "python -m venv .venv" in t
    assert "pip install -e ." in t
    assert "desi doctor" in t


def test_dummies_has_both_os_activation() -> None:
    t = _read("INSTALL_DUMMIES.md")
    assert ".venv\\Scripts\\activate" in t          # Windows
    assert "source .venv/bin/activate" in t          # macOS/Linux


def test_quickstart_and_install_have_minimal_commands() -> None:
    for name in ("QUICKSTART.md", "INSTALL.md"):
        t = _read(name)
        assert "pip install -e ." in t
        assert "python -m venv .venv" in t
        assert ".venv\\Scripts\\activate" in t
        assert "source .venv/bin/activate" in t


# --- ELI5 honesty -------------------------------
def test_eli5_states_what_desi_is_not() -> None:
    # strip markdown emphasis so phrasing checks are robust
    t = _read("docs/ELI5_DESi.md").lower().replace("*", "")
    assert "not a new language model" in t
    assert "does not replace" in t
    assert "not a general thinking machine" in t
    # the forbidden over-claims must appear only inside denials
    assert "does not" in t and "solve truth" in t
    assert "not prevent all hallucinations" in t


def test_eli5_explains_hallucination_visibility() -> None:
    t = _read("docs/ELI5_DESi.md").lower()
    assert "visible" in t
    assert "magically impossible" in t or "not make hallucinations" in t


# --- scripts ------------------------------------
def test_install_scripts_present_and_keyless() -> None:
    sh = _read("scripts/install_dev.sh")
    ps = _read("scripts/install_dev.ps1")
    for s in (sh, ps):
        assert "pip install -e ." in s
        assert "desi doctor" in s
        # never ask for or store a key
        assert "api_key" not in s.lower()
        assert "sk-or" not in s
