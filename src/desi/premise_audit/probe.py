"""Aufgabe 5 — per-signal masking probe.

For each of the 11 extraction signals we compute:

* baseline_separability — Euclidean distance between the valid
  and adversarial centroids in the full 11-dim feature space;
* masked_separability — same distance computed with the target
  signal masked (set to the valid-mean value);
* delta = baseline - masked.

A signal whose ``delta < 0.10`` is a DEAD_KNOB (no useful
contribution); a signal whose ``delta > 0.50`` is a
PRIMARY_SIGNAL (carries the bulk of the discrimination).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .signals import SIGNAL_ORDER, ExtractionSignals, extract_signals


DEAD_KNOB_DELTA: float = 0.10
PRIMARY_SIGNAL_DELTA: float = 0.50


def _mean_vec(rows: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    if not rows:
        return tuple([0.0] * 11)
    dim = len(rows[0])
    sums = [0.0] * dim
    for r in rows:
        for i, x in enumerate(r):
            sums[i] += x
    return tuple(s / len(rows) for s in sums)


def _norm(v: tuple[float, ...]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _diff(a: tuple[float, ...],
          b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(bi - ai for ai, bi in zip(a, b))


def _saturate(raw: float) -> float:
    # Match the v3.19 saturation: |·|/10 capped at 1.
    return round(min(1.0, raw / 10.0), 6)


def _separability(
    valid_rows: tuple[tuple[float, ...], ...],
    adv_rows: tuple[tuple[float, ...], ...],
) -> float:
    if not valid_rows or not adv_rows:
        return 0.0
    v = _mean_vec(valid_rows)
    a = _mean_vec(adv_rows)
    return _saturate(_norm(_diff(v, a)))


def _mask(rows: tuple[tuple[float, ...], ...], idx: int,
          replacement: float) -> tuple[tuple[float, ...], ...]:
    out: list[tuple[float, ...]] = []
    for r in rows:
        lst = list(r)
        lst[idx] = replacement
        out.append(tuple(lst))
    return tuple(out)


@dataclass(frozen=True)
class SignalProbe:
    signal: str
    baseline_separability: float
    masked_separability: float
    delta: float
    classification: str   # "PRIMARY_SIGNAL", "DEAD_KNOB", "NEUTRAL"

    def to_dict(self) -> dict[str, object]:
        return {
            "signal": self.signal,
            "baseline_separability": self.baseline_separability,
            "masked_separability": self.masked_separability,
            "delta": self.delta,
            "classification": self.classification,
        }


def run_per_signal_probe(
    valid_signals: tuple[ExtractionSignals, ...],
    adv_signals: tuple[ExtractionSignals, ...],
) -> tuple[SignalProbe, ...]:
    valid_rows = tuple(s.feature_tuple() for s in valid_signals)
    adv_rows = tuple(s.feature_tuple() for s in adv_signals)
    baseline = _separability(valid_rows, adv_rows)
    valid_mean = _mean_vec(valid_rows)

    out: list[SignalProbe] = []
    # The feature tuple skips the kind_sequence list; the order
    # matches SIGNAL_ORDER minus the categorical entry.
    feature_signals = [
        s for s in SIGNAL_ORDER if s != "premise_kind_sequence"
    ]
    for idx, name in enumerate(feature_signals):
        masked_valid = _mask(valid_rows, idx, valid_mean[idx])
        masked_adv = _mask(adv_rows, idx, valid_mean[idx])
        masked = _separability(masked_valid, masked_adv)
        delta = round(baseline - masked, 6)
        if delta < DEAD_KNOB_DELTA:
            cls = "DEAD_KNOB"
        elif delta > PRIMARY_SIGNAL_DELTA:
            cls = "PRIMARY_SIGNAL"
        else:
            cls = "NEUTRAL"
        out.append(SignalProbe(
            signal=name,
            baseline_separability=baseline,
            masked_separability=masked,
            delta=delta,
            classification=cls,
        ))
    return tuple(out)


__all__ = [
    "DEAD_KNOB_DELTA",
    "PRIMARY_SIGNAL_DELTA",
    "SignalProbe",
    "run_per_signal_probe",
]
