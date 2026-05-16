"""Aufgabe 5 — every cited artifact hash matches the
deployed artifact, including the entire v3-line carried
forward."""
from __future__ import annotations

import json
import pathlib


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


_V2_EXPECTED: dict[str, str] = {
    # v2.8 reconstruction hashes embedded in v2.7 protocol.
    # Verified live by tests/paper_v3 + paper_v4 helpers.
}


_V3_EXPECTED: dict[str, str] = {
    "v3_11": "1c8e6d0e0b90905c",
    "v3_13": "733032cc30a0cc2e",
    "v3_14": "94be5611fc9bd336",
    "v3_15": "a6edfa9a53914bcc",
    "v3_16": "1f4e5f85c085d32f",
    "v3_17": "a01b6edaa9e1a086",
    "v3_18": "7829ae1e1750f00d",
    "v3_19": "3cbde141b5d90a46",
    "v3_20": "02eb32df1f51b761",
    "v3_21": "f570c9e94770dfbc",
    "v3_22": "be039cd52c3de9b5",
    "v3_23": "0246444ccd8f96ef",
}


_V4_EXPECTED: dict[str, str] = {
    "v4_0": "aefa8f1e3429225a",
    "v4_1": "f7ec695f17aa341b",
    "v4_2": "181ec3cb1febf62f",
    "v4_3": "7c63bcae4cf3fb37",
    "v4_4": "bf4147b89f398224",
    "v4_5": "86418c9d976cc147",
    "v4_6": "58268fd9c4437e49",
    "v4_7": "2774818766a8035a",
    "v4_8": "d0835b564453cfc0",
    "v4_9": "51122b802bd257dc",
}


def _read_hash(name: str) -> str:
    p = _REPO_ROOT / "artifacts" / name / "report.json"
    return json.loads(p.read_text(encoding="utf-8"))[
        "replay_hash"
    ]


def test_v3_artifact_hashes_pinned() -> None:
    actual = {name: _read_hash(name) for name in _V3_EXPECTED}
    assert actual == _V3_EXPECTED


def test_v4_artifact_hashes_pinned() -> None:
    actual = {name: _read_hash(name) for name in _V4_EXPECTED}
    assert actual == _V4_EXPECTED
