"""v3.53 — cross-corpus radius transfer report.

Pflichtmetriken (directive § v3.53):

* ``corpus_radius_breaks``   — per-corpus boolean,
  does the v3.44 step function survive?
* ``corpus_critical_radii``  — per-corpus smallest
  radius at which leakage reaches half-population
* ``radius_transfer_rate``   — fraction of present
  corpora whose break survives
* ``artifact_likelihoods``   — per-corpus
  artifact_likelihood from the v3.49 mask sweep
* ``replay_stability``       — deterministic two-run
  equality
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import inf

from ..frame_artifact_audit.mask import MaskKind
from .corpus_loader import (
    REFERENCE_CORPORA, corpus_present,
)
from .radius_transfer import (
    CorpusRadiusRecord, per_corpus_critical_radius,
    per_corpus_radius_record,
)


PAPER11_TRANSFER_FLOOR: float = 0.75


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _radius_label_or_inf(r: float | None) -> str | None:
    if r is None:
        return None
    if r == inf or r == float("inf"):
        return "inf"
    return f"{r:g}"


@dataclass(frozen=True)
class V353Report:
    corpora_present: tuple[str, ...]
    corpora_missing: tuple[str, ...]
    per_corpus_records: tuple[dict, ...]
    corpus_radius_breaks: dict[str, bool]
    corpus_critical_radii: dict[str, str | None]
    radius_transfer_rate: float
    artifact_likelihoods: dict[str, float]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "corpora_present":
                list(self.corpora_present),
            "corpora_missing":
                list(self.corpora_missing),
            "per_corpus_records":
                list(self.per_corpus_records),
            "corpus_radius_breaks":
                dict(self.corpus_radius_breaks),
            "corpus_critical_radii":
                dict(self.corpus_critical_radii),
            "radius_transfer_rate":
                self.radius_transfer_rate,
            "artifact_likelihoods":
                dict(self.artifact_likelihoods),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


_FRAME_MASKS = (
    MaskKind.FRAME_AT_2.value,
    MaskKind.FRAME_FULL.value,
    MaskKind.FRAME_PERMUTED.value,
)


def _per_corpus_records() -> tuple[CorpusRadiusRecord, ...]:
    out: list[CorpusRadiusRecord] = []
    for c in REFERENCE_CORPORA:
        if not corpus_present(c):
            continue
        for m in (MaskKind.NONE.value, *_FRAME_MASKS,
                  MaskKind.SUPPORT_ONLY.value,
                  MaskKind.GEOMETRY_ONLY.value):
            out.append(
                per_corpus_radius_record(c, m),
            )
    return tuple(out)


def _artifact_likelihood_per_corpus(
    records: tuple[CorpusRadiusRecord, ...],
) -> dict[str, float]:
    """Per-corpus collapse rate across non-identity
    masks (matches the v3.49 definition)."""
    by_corpus: dict[str, list[CorpusRadiusRecord]] = {}
    for r in records:
        if r.mask == MaskKind.NONE.value:
            continue
        by_corpus.setdefault(r.corpus, []).append(r)
    out: dict[str, float] = {}
    for c, rs in by_corpus.items():
        if not rs:
            out[c] = 0.0
            continue
        collapsed = sum(
            1 for r in rs
            if not r.radius_break_survives
        )
        out[c] = _round(collapsed / len(rs))
    return out


def _replay_stability() -> float:
    a = [r.to_dict() for r in _per_corpus_records()]
    b = [r.to_dict() for r in _per_corpus_records()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V353Report:
    present = tuple(
        c for c in REFERENCE_CORPORA
        if corpus_present(c)
    )
    missing = tuple(
        c for c in REFERENCE_CORPORA
        if not corpus_present(c)
    )
    records = _per_corpus_records()
    # corpus_radius_breaks is the no-mask
    # (identity) survival per corpus.
    breaks: dict[str, bool] = {}
    for r in records:
        if r.mask == MaskKind.NONE.value:
            breaks[r.corpus] = r.radius_break_survives
    crits: dict[str, str | None] = {}
    for c in present:
        crits[c] = _radius_label_or_inf(
            per_corpus_critical_radius(c),
        )
    if breaks:
        rate = _round(
            sum(1 for v in breaks.values() if v)
            / len(breaks),
        )
    else:
        rate = 0.0
    artifact = _artifact_likelihood_per_corpus(records)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate >= PAPER11_TRANSFER_FLOOR:
        verdict = "RADIUS_TRANSFER_HOLDS"
    elif rate >= 0.50:
        verdict = "RADIUS_TRANSFER_PARTIAL"
    else:
        verdict = "RADIUS_TRANSFER_LOCAL"

    rationale = (
        f"INFO: corpora_present "
        f"{list(present)}",
        f"INFO: corpora_missing "
        f"{list(missing) or '[]'}",
        f"INFO: corpus_radius_breaks "
        f"{sorted(breaks.items())}",
        f"INFO: corpus_critical_radii "
        f"{sorted(crits.items())}",
        f"INFO: artifact_likelihoods "
        f"{sorted(artifact.items())}",
        f"{'PASS' if rate >= PAPER11_TRANSFER_FLOOR else 'FAIL'}: "
        f"radius_transfer_rate {rate} >= "
        f"{PAPER11_TRANSFER_FLOOR}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V353Report(
        corpora_present=present,
        corpora_missing=missing,
        per_corpus_records=tuple(
            r.to_dict() for r in records
        ),
        corpus_radius_breaks=breaks,
        corpus_critical_radii=crits,
        radius_transfer_rate=rate,
        artifact_likelihoods=artifact,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cross_corpus_radius_artifact(
) -> dict[str, object]:
    records = _per_corpus_records()
    return {
        "schema_version":
            "v3_53_cross_corpus_radius",
        "corpora_present": [
            c for c in REFERENCE_CORPORA
            if corpus_present(c)
        ],
        "records": [r.to_dict() for r in records],
    }


__all__ = [
    "PAPER11_TRANSFER_FLOOR", "V353Report",
    "build_cross_corpus_radius_artifact",
    "build_report",
]
