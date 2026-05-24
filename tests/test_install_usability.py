"""Install-usability GO/NO-GO assessment tests."""
from __future__ import annotations

import pathlib

from desi.install_usability import (
    assessment, build_go_no_go, is_go,
)
from desi.install_usability.report import (
    governance_invariants_touched, replay_invariants_touched,
)

_ART = (
    pathlib.Path(__file__).resolve().parents[1]
    / "artifacts" / "install_usability"
    / "install_usability_go_no_go.md"
)


def test_assessment_is_go() -> None:
    assert is_go() is True


def test_no_invariants_touched() -> None:
    assert replay_invariants_touched() is False
    assert governance_invariants_touched() is False


def test_all_usability_checks_pass() -> None:
    a = assessment()
    assert a["install_docs_created"] is True
    assert a["dummy_install_path_works"] is True
    assert a["config_loader_works"] is True
    assert a["secrets_protected"] is True
    assert a["offline_default_preserved"] is True


def test_go_no_go_artifact_present_and_go() -> None:
    assert _ART.exists()
    text = _ART.read_text(encoding="utf-8")
    assert "`GO`" in text
    assert "replay-governance wins" in text


def test_go_no_go_matches_live_build() -> None:
    assert _ART.read_text(encoding="utf-8") == build_go_no_go()
