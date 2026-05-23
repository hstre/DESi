"""v3.84 — calibration of the pairwise forecast.

* Map ``score = -distance`` to a predicted
  probability via min-max normalisation onto [0, 1].
* Bin the pairs into ``CALIBRATION_BIN_COUNT``
  equal-width score bins.
* ``calibration_error`` is the weighted mean
  absolute deviation between each bin's mean
  predicted probability and the bin's empirical
  positive rate (Expected Calibration Error).
"""
from __future__ import annotations

from dataclasses import dataclass

from .forecast import (
    PairForecast, all_pair_forecasts,
)


CALIBRATION_BIN_COUNT: int = 5


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


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
            "mean_predicted": self.mean_predicted,
            "actual_positive_rate":
                self.actual_positive_rate,
        }


def calibration_bins() -> tuple[
    CalibrationBin, ...,
]:
    pairs = all_pair_forecasts()
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
            tuple[PairForecast, float]
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
            1 for p, _ in sel if p.same_class
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
    """Expected Calibration Error over the
    population of pairs. Lower = better
    calibration."""
    bins = calibration_bins()
    total = sum(b.count for b in bins)
    if total == 0:
        return 0.0
    err = 0.0
    for b in bins:
        if b.count == 0:
            continue
        err += (b.count / total) * abs(
            b.mean_predicted - b.actual_positive_rate
        )
    return _round(err)


__all__ = [
    "CALIBRATION_BIN_COUNT", "CalibrationBin",
    "calibration_bins", "calibration_error",
]
