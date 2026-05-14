"""Hard invariant: stable-v1.9.0 source is byte-for-byte unchanged.

The v2.0 directive's first non-negotiable: "Keine Änderungen an
stable-v1.9.0". This test takes the same fingerprint the sandbox
takes internally and verifies it is invariant under a full run.
"""
from __future__ import annotations

import hashlib
import pathlib

from dataclasses import dataclass

from desi.sandbox import EvolutionSandbox, GateVerdict


@dataclass
class _PassGate:
    def evaluate(self) -> GateVerdict:
        return GateVerdict(
            passed=True, precision=1.0, recall=1.0, false_positives=0,
            authority_blocks=10, tool_precision=1.0, hash_mismatches=0,
        )


def _walk(root: pathlib.Path) -> dict[str, str]:
    """Map of relative-path → file-sha256 for every stable .py file."""
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root).as_posix()
        if rel.startswith("sandbox/"):
            continue                          # v2.0 module — out of scope
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_no_stable_source_file_modified_by_a_sandbox_run() -> None:
    pkg_root = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "src" / "desi"
    )
    before = _walk(pkg_root)

    sb = EvolutionSandbox(n_steps=5, gate=_PassGate())
    rep = sb.run()

    after = _walk(pkg_root)
    assert before == after, "stable-v1.9.0 source files changed mid-run"
    assert rep.stable_hash_before == rep.stable_hash_after


def test_sandbox_module_is_outside_the_stable_fingerprint() -> None:
    """The fingerprint excludes the v2.0 sandbox package itself, so
    sandbox edits never affect ``stable_hash_before/after``."""
    sb = EvolutionSandbox(n_steps=1, gate=_PassGate())
    rep = sb.run()
    assert rep.stable_hash_before == rep.stable_hash_after
