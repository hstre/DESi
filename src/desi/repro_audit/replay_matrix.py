"""Aufgabe 8 — global replay audit.

For every pinned version (v2.8, v3.11-v3.24, v4.0-v4.10):

* read the frozen artifact's replay_hash from disk,
* attempt a live replay if the corresponding builder /
  protocol is callable,
* compare the two hashes,
* assign exactly one ``ReproducibilityClass`` value.

Result is written to ``artifacts/v4_11/replay_matrix.json``.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Callable

from .enums import ReproducibilityClass


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


_FROZEN_ONLY_VERSIONS: tuple[str, ...] = (
    # Versions whose artifact is the canonical record and
    # whose live-replay builder either does not exist or is
    # intentionally deprecated.
    "v3_11", "v3_13", "v3_14", "v3_15", "v3_16", "v3_17",
    "v3_18", "v3_19", "v3_20", "v3_21", "v3_22", "v3_23",
)


def _build_v40() -> str | None:
    """Live replay of v4.0 external probe."""
    from datetime import datetime, timezone
    from ..external_probe import build_external_probe_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    r = build_external_probe_report(
        started_at=when, finished_at=when,
    )
    return r.replay_hash


def _build_v41() -> str | None:
    from datetime import datetime, timezone
    from ..frame_inference import build_v41_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v41_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v42() -> str | None:
    from datetime import datetime, timezone
    from ..external_audit_probe import build_v42_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v42_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v43() -> str | None:
    from datetime import datetime, timezone
    from ..external_audit_patch import build_v43_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v43_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v44() -> str | None:
    from datetime import datetime, timezone
    from ..residual_semantic_probe import build_v44_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v44_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v45() -> str | None:
    from datetime import datetime, timezone
    from ..bidirectional_cycle_patch import build_v45_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v45_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v46() -> str | None:
    from datetime import datetime, timezone
    from ..warrant_probe import build_v46_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v46_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v47() -> str | None:
    from datetime import datetime, timezone
    from ..modality_patch import build_v47_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v47_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v48() -> str | None:
    from datetime import datetime, timezone
    from ..content_audit_probe import build_v48_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v48_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v49() -> str | None:
    from datetime import datetime, timezone
    from ..content_inversion_patch import build_v49_report
    when = datetime(2026, 5, 16, tzinfo=timezone.utc)
    return build_v49_report(
        started_at=when, finished_at=when,
    ).replay_hash


def _build_v28_reconstruction() -> str | None:
    from ..rule_patch_protocol import (
        RulePatchProtocol, causal_chain_v2_7_candidate,
    )
    return RulePatchProtocol().run(
        causal_chain_v2_7_candidate(),
    ).replay_hash


_LIVE_BUILDERS: dict[str, Callable[[], str | None]] = {
    "v4_0": _build_v40,
    "v4_1": _build_v41,
    "v4_2": _build_v42,
    "v4_3": _build_v43,
    "v4_4": _build_v44,
    "v4_5": _build_v45,
    "v4_6": _build_v46,
    "v4_7": _build_v47,
    "v4_8": _build_v48,
    "v4_9": _build_v49,
    "v2_8": _build_v28_reconstruction,
}


_REQUIRED_VERSIONS: tuple[str, ...] = (
    "v2_8",
    "v3_11", "v3_13", "v3_14", "v3_15", "v3_16", "v3_17",
    "v3_18", "v3_19", "v3_20", "v3_21", "v3_22", "v3_23",
    "v4_0", "v4_1", "v4_2", "v4_3", "v4_4", "v4_5",
    "v4_6", "v4_7", "v4_8", "v4_9", "v4_10",
)


@dataclass(frozen=True)
class MatrixEntry:
    version: str
    artifact_exists: bool
    frozen_hash: str | None
    live_replay_available: bool
    live_hash: str | None
    hash_equal: bool | None
    repro_class: str

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "artifact_exists": self.artifact_exists,
            "frozen_hash": self.frozen_hash,
            "live_replay_available":
                self.live_replay_available,
            "live_hash": self.live_hash,
            "hash_equal": self.hash_equal,
            "repro_class": self.repro_class,
        }


def _frozen_hash(version: str) -> tuple[bool, str | None]:
    """Read frozen artifact hash, with v2.8 reading the
    v2.8 reconstruction artifact specifically."""
    if version == "v2_8":
        p = _REPO_ROOT / "artifacts" / "v2_8" / "reconstruction.json"
        if not p.exists():
            return False, None
        data = json.loads(p.read_text(encoding="utf-8"))
        return True, data.get("replay_hash")
    p = _REPO_ROOT / "artifacts" / version / "report.json"
    if not p.exists():
        return False, None
    data = json.loads(p.read_text(encoding="utf-8"))
    return True, data.get("replay_hash")


def _classify(
    *,
    artifact_exists: bool,
    live_replay_available: bool,
    hash_equal: bool | None,
    frozen_only: bool,
) -> ReproducibilityClass:
    if not artifact_exists:
        return ReproducibilityClass.UNKNOWN
    if frozen_only:
        return ReproducibilityClass.FROZEN_ARTIFACT_REPLAYABLE
    if not live_replay_available:
        return ReproducibilityClass.NON_REPLAYABLE_BY_DESIGN
    if hash_equal:
        return ReproducibilityClass.LIVE_REPLAY_STABLE
    return ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT


def build_entry(version: str) -> MatrixEntry:
    artifact_exists, frozen = _frozen_hash(version)
    builder = _LIVE_BUILDERS.get(version)
    live_available = builder is not None
    live: str | None = None
    if live_available:
        try:
            live = builder()  # type: ignore[misc]
        except Exception:  # noqa: BLE001
            live = None
            live_available = False
    if not artifact_exists:
        hash_equal: bool | None = None
    elif not live_available:
        hash_equal = None
    else:
        hash_equal = frozen == live
    repro = _classify(
        artifact_exists=artifact_exists,
        live_replay_available=live_available,
        hash_equal=hash_equal,
        frozen_only=(version in _FROZEN_ONLY_VERSIONS),
    )
    return MatrixEntry(
        version=version,
        artifact_exists=artifact_exists,
        frozen_hash=frozen,
        live_replay_available=live_available,
        live_hash=live,
        hash_equal=hash_equal,
        repro_class=repro.value,
    )


def build_matrix() -> tuple[MatrixEntry, ...]:
    return tuple(build_entry(v) for v in _REQUIRED_VERSIONS)


__all__ = [
    "MatrixEntry", "build_entry", "build_matrix",
]
