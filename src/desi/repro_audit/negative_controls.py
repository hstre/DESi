"""Aufgabe 10 — 20 reproducibility classification fixtures.

Each fixture asserts that a synthetic
(artifact_exists, live_replay_available, hash_equal,
frozen_only) tuple maps to the expected
``ReproducibilityClass`` value.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ReproducibilityClass
from .replay_matrix import _classify


@dataclass(frozen=True)
class ReproNC:
    nc_id: str
    artifact_exists: bool
    live_replay_available: bool
    hash_equal: bool | None
    frozen_only: bool
    expected_class: str
    rationale: str


_FIXTURES: tuple[ReproNC, ...] = (
    # FROZEN_ARTIFACT_REPLAYABLE — frozen-only versions.
    ReproNC(
        "NC-001", True, False, None, True,
        ReproducibilityClass.FROZEN_ARTIFACT_REPLAYABLE.value,
        "frozen-only artifact has no live builder",
    ),
    ReproNC(
        "NC-002", True, True, True, True,
        ReproducibilityClass.FROZEN_ARTIFACT_REPLAYABLE.value,
        "frozen-only flag wins even if a live builder exists",
    ),
    ReproNC(
        "NC-003", True, False, None, True,
        ReproducibilityClass.FROZEN_ARTIFACT_REPLAYABLE.value,
        "frozen-only artifact with no live coverage",
    ),
    # LIVE_REPLAY_STABLE — live equals frozen.
    ReproNC(
        "NC-004", True, True, True, False,
        ReproducibilityClass.LIVE_REPLAY_STABLE.value,
        "live and frozen hashes match",
    ),
    ReproNC(
        "NC-005", True, True, True, False,
        ReproducibilityClass.LIVE_REPLAY_STABLE.value,
        "another live-stable case",
    ),
    ReproNC(
        "NC-006", True, True, True, False,
        ReproducibilityClass.LIVE_REPLAY_STABLE.value,
        "yet another live-stable case",
    ),
    # HISTORICAL_RUNTIME_DRIFT — live differs from frozen.
    ReproNC(
        "NC-007", True, True, False, False,
        ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT.value,
        "live rebuild differs from frozen artifact",
    ),
    ReproNC(
        "NC-008", True, True, False, False,
        ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT.value,
        "drift on a non-frozen-only artifact",
    ),
    ReproNC(
        "NC-009", True, True, False, False,
        ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT.value,
        "third drift fixture",
    ),
    ReproNC(
        "NC-010", True, True, False, False,
        ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT.value,
        "fourth drift fixture",
    ),
    # NON_REPLAYABLE_BY_DESIGN — frozen exists, no live builder.
    ReproNC(
        "NC-011", True, False, None, False,
        ReproducibilityClass.NON_REPLAYABLE_BY_DESIGN.value,
        "no live builder available (e.g. consolidation report)",
    ),
    ReproNC(
        "NC-012", True, False, None, False,
        ReproducibilityClass.NON_REPLAYABLE_BY_DESIGN.value,
        "frozen artifact without builder hook",
    ),
    ReproNC(
        "NC-013", True, False, None, False,
        ReproducibilityClass.NON_REPLAYABLE_BY_DESIGN.value,
        "intentionally non-replayable historical record",
    ),
    # UNKNOWN — missing artifact.
    ReproNC(
        "NC-014", False, False, None, False,
        ReproducibilityClass.UNKNOWN.value,
        "missing artifact, no live builder",
    ),
    ReproNC(
        "NC-015", False, True, None, False,
        ReproducibilityClass.UNKNOWN.value,
        "missing artifact even though a live builder exists",
    ),
    ReproNC(
        "NC-016", False, False, None, True,
        ReproducibilityClass.UNKNOWN.value,
        "missing artifact flagged frozen-only",
    ),
    ReproNC(
        "NC-017", False, True, True, False,
        ReproducibilityClass.UNKNOWN.value,
        "missing artifact even with apparent live match",
    ),
    # Additional environment-dependent / drift mix.
    ReproNC(
        "NC-018", True, True, False, False,
        ReproducibilityClass.HISTORICAL_RUNTIME_DRIFT.value,
        "drift confirmed across both halves",
    ),
    ReproNC(
        "NC-019", True, True, True, False,
        ReproducibilityClass.LIVE_REPLAY_STABLE.value,
        "live-stable confirmation",
    ),
    ReproNC(
        "NC-020", True, False, None, True,
        ReproducibilityClass.FROZEN_ARTIFACT_REPLAYABLE.value,
        "frozen-only without live coverage",
    ),
)


def all_repro_ncs() -> tuple[ReproNC, ...]:
    return _FIXTURES


def classify_nc(nc: ReproNC) -> str:
    return _classify(
        artifact_exists=nc.artifact_exists,
        live_replay_available=nc.live_replay_available,
        hash_equal=nc.hash_equal,
        frozen_only=nc.frozen_only,
    ).value


def classification_accuracy() -> float:
    correct = sum(
        1 for nc in _FIXTURES
        if classify_nc(nc) == nc.expected_class
    )
    return round(correct / len(_FIXTURES), 6)


__all__ = [
    "ReproNC", "all_repro_ncs", "classification_accuracy",
    "classify_nc",
]
