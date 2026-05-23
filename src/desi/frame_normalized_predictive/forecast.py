"""v3.92 — forecast metrics on frame-normalized
novel pairs.

Mirrors the v3.88 / v3.84 template so the v3.85-
v3.92 chain shares one methodology.
"""
from __future__ import annotations

from dataclasses import dataclass

from .predict import (
    FrameNormalizedPairForecast,
    all_normalized_pair_forecasts,
)


CALIBRATION_BIN_COUNT: int = 5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def roc_auc(
    pairs: tuple[FrameNormalizedPairForecast, ...],
) -> float:
    pos = [
        p.score for p in pairs if p.same_family
    ]
    neg = [
        p.score for p in pairs
        if not p.same_family
    ]
    if not pos or not neg:
        return 0.5
    wins = 0
    ties = 0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1
            elif sp == sn:
                ties += 1
    total = len(pos) * len(neg)
    return _round((wins + 0.5 * ties) / total)


def frame_normalized_auc() -> float:
    return roc_auc(all_normalized_pair_forecasts())


def forecast_margin() -> float:
    pairs = all_normalized_pair_forecasts()
    pos = [
        p.score for p in pairs if p.same_family
    ]
    neg = [
        p.score for p in pairs
        if not p.same_family
    ]
    if not pos or not neg:
        return 0.0
    return _round(min(pos) - max(neg))


def optimal_threshold() -> float:
    pairs = all_normalized_pair_forecasts()
    pos = [
        p.score for p in pairs if p.same_family
    ]
    neg = [
        p.score for p in pairs
        if not p.same_family
    ]
    if not pos or not neg:
        return 0.0
    return _round((min(pos) + max(neg)) / 2.0)


def frame_normalized_fpr(
    threshold: float,
) -> float:
    pairs = all_normalized_pair_forecasts()
    neg = [p for p in pairs if not p.same_family]
    if not neg:
        return 0.0
    fp = sum(
        1 for p in neg if p.score >= threshold
    )
    return _round(fp / len(neg))


def _to_prob(
    score: float, lo: float, hi: float,
) -> float:
    if hi <= lo:
        return 0.5
    return (score - lo) / (hi - lo)


@dataclass(frozen=True)
class CalibrationBin:
    bin_index: int
    lower: float
    upper: float
    count: int
    mean_predicted: float
    actual_positive_rate: float

    def to_dict(self) -> dict[str, object]:
        return {
            "bin_index": self.bin_index,
            "lower": self.lower,
            "upper": self.upper,
            "count": self.count,
            "mean_predicted":
                self.mean_predicted,
            "actual_positive_rate":
                self.actual_positive_rate,
        }


def calibration_bins() -> tuple[
    CalibrationBin, ...,
]:
    pairs = all_normalized_pair_forecasts()
    if not pairs:
        return ()
    scores = [p.score for p in pairs]
    lo = min(scores)
    hi = max(scores)
    probs = [_to_prob(s, lo, hi) for s in scores]
    width = 1.0 / CALIBRATION_BIN_COUNT
    bins: list[CalibrationBin] = []
    for i in range(CALIBRATION_BIN_COUNT):
        b_lo = i * width
        b_hi = (i + 1) * width
        sel: list[
            tuple[FrameNormalizedPairForecast, float]
        ] = []
        for p, q in zip(pairs, probs):
            if i == CALIBRATION_BIN_COUNT - 1:
                if b_lo <= q <= b_hi:
                    sel.append((p, q))
            elif b_lo <= q < b_hi:
                sel.append((p, q))
        if not sel:
            bins.append(CalibrationBin(
                bin_index=i,
                lower=_round(b_lo),
                upper=_round(b_hi),
                count=0,
                mean_predicted=_round(
                    (b_lo + b_hi) / 2.0,
                ),
                actual_positive_rate=0.0,
            ))
            continue
        mean_pred = sum(
            q for _, q in sel
        ) / len(sel)
        pos = sum(
            1 for p, _ in sel if p.same_family
        )
        rate = pos / len(sel)
        bins.append(CalibrationBin(
            bin_index=i,
            lower=_round(b_lo),
            upper=_round(b_hi),
            count=len(sel),
            mean_predicted=_round(mean_pred),
            actual_positive_rate=_round(rate),
        ))
    return tuple(bins)


def calibration_error() -> float:
    bins = calibration_bins()
    total = sum(b.count for b in bins)
    if total == 0:
        return 0.0
    err = 0.0
    for b in bins:
        if b.count == 0:
            continue
        err += (b.count / total) * abs(
            b.mean_predicted
            - b.actual_positive_rate
        )
    return _round(err)


__all__ = [
    "CALIBRATION_BIN_COUNT", "CalibrationBin",
    "calibration_bins", "calibration_error",
    "forecast_margin", "frame_normalized_auc",
    "frame_normalized_fpr",
    "optimal_threshold", "roc_auc",
]
