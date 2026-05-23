"""v15.1 - longitudinal narrative-trajectory
fixture and the narrative_drift signal.

This layer sits on top of the v15.0 DAX corpus
(same firm codenames, same post-hoc labels - all
illustrative-synthetic, never named real
companies). It models, per firm per year, how the
MANAGEMENT NARRATIVE is distributed over a closed
set of themes, and how forward-looking claims and
disclosure bridges evolve.

narrative_drift measures how far the theme
distribution moves year over year. High drift is
an audit-worthy signal that the story is being
re-told - NOT a fraud claim.

Reads only the synthetic narrative trajectory.
The post-hoc label is read solely by the
validators in report.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from desi.financial_governance import firms


class Theme(str, Enum):
    """Closed set of management-narrative themes."""
    GROWTH               = "growth"
    PROFITABILITY        = "profitability"
    COMPLIANCE           = "compliance"
    RISK_TRANSPARENCY    = "risk_transparency"
    INNOVATION           = "innovation"
    GEOGRAPHIC_EXPANSION = "geographic_expansion"


THEMES: tuple[str, ...] = tuple(t.value for t in Theme)

# Themes a firm under pressure tends to drift AWAY
# from (sober disclosure) ...
_SOBER = (Theme.RISK_TRANSPARENCY, Theme.COMPLIANCE)
# ... and the themes it tends to drift TOWARD
# (upbeat reframing).
_UPBEAT = (Theme.GROWTH, Theme.INNOVATION)

_N_YEARS = 10
_START_YEAR = 2011


@dataclass(frozen=True)
class _TrajProfile:
    firm_id: str
    drift_rate: float        # per-year interpolation toward spin target
    claim_fulfilment: float  # fraction of forward claims upheld
    bridge_required: tuple[int, int]   # (start, end)
    bridge_provided: tuple[int, int]   # (start, end)


# Per-firm trajectory archetypes, keyed by the
# v15.0 firm codenames.
_TRAJ: dict[str, _TrajProfile] = {
    "PAYMENTS_ALPHA": _TrajProfile(
        "PAYMENTS_ALPHA", drift_rate=0.085,
        claim_fulfilment=0.30,
        bridge_required=(4, 12),
        bridge_provided=(3, 3),
    ),
    "AUTO_BETA": _TrajProfile(
        "AUTO_BETA", drift_rate=0.045,
        claim_fulfilment=0.60,
        bridge_required=(5, 9),
        bridge_provided=(4, 5),
    ),
    "CHEM_GAMMA": _TrajProfile(
        "CHEM_GAMMA", drift_rate=0.004,
        claim_fulfilment=1.00,
        bridge_required=(5, 5),
        bridge_provided=(5, 5),
    ),
    "UTILITY_DELTA": _TrajProfile(
        "UTILITY_DELTA", drift_rate=0.002,
        claim_fulfilment=1.00,
        bridge_required=(5, 5),
        bridge_provided=(5, 5),
    ),
    "PHARMA_EPSILON": _TrajProfile(
        "PHARMA_EPSILON", drift_rate=0.012,
        claim_fulfilment=0.85,
        bridge_required=(5, 7),
        bridge_provided=(5, 6),
    ),
    "INDUSTRIAL_ZETA": _TrajProfile(
        "INDUSTRIAL_ZETA", drift_rate=0.003,
        claim_fulfilment=1.00,
        bridge_required=(5, 5),
        bridge_provided=(5, 5),
    ),
}


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


# Baseline (sober) and spin-target distributions
# over the six themes, in Theme declaration order.
_BASE = {
    Theme.GROWTH: 0.18,
    Theme.PROFITABILITY: 0.18,
    Theme.COMPLIANCE: 0.20,
    Theme.RISK_TRANSPARENCY: 0.22,
    Theme.INNOVATION: 0.12,
    Theme.GEOGRAPHIC_EXPANSION: 0.10,
}
_SPIN = {
    Theme.GROWTH: 0.34,
    Theme.PROFITABILITY: 0.20,
    Theme.COMPLIANCE: 0.06,
    Theme.RISK_TRANSPARENCY: 0.05,
    Theme.INNOVATION: 0.27,
    Theme.GEOGRAPHIC_EXPANSION: 0.08,
}


def _weights_at(
    p: _TrajProfile, t: int,
) -> dict[Theme, float]:
    """Convex blend of baseline and spin target;
    the blend coefficient grows with the year."""
    a = _clip01(p.drift_rate * t)
    return {
        th: (1.0 - a) * _BASE[th] + a * _SPIN[th]
        for th in Theme
    }


@dataclass(frozen=True)
class NarrativeYear:
    firm_id: str
    fiscal_year: int
    theme_weights: tuple[tuple[str, float], ...]
    bridges_required: int
    bridges_provided: int

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "fiscal_year": self.fiscal_year,
            "theme_weights": [
                [k, round(v, 6)]
                for k, v in self.theme_weights
            ],
            "bridges_required":
                self.bridges_required,
            "bridges_provided":
                self.bridges_provided,
        }


@dataclass(frozen=True)
class NarrativeTrajectory:
    firm_id: str
    sector: str
    post_hoc_label: str
    years: tuple[NarrativeYear, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "post_hoc_label": self.post_hoc_label,
            "years": [
                y.to_dict() for y in self.years
            ],
        }


def _lerp_int(a: int, b: int, t: int) -> int:
    if _N_YEARS <= 1:
        return a
    frac = t / (_N_YEARS - 1)
    return int(round(a + (b - a) * frac))


def _build(firm) -> NarrativeTrajectory:  # noqa: ANN001
    p = _TRAJ[firm.firm_id]
    rows: list[NarrativeYear] = []
    for t in range(_N_YEARS):
        w = _weights_at(p, t)
        rows.append(NarrativeYear(
            firm_id=firm.firm_id,
            fiscal_year=_START_YEAR + t,
            theme_weights=tuple(
                (th.value, w[th]) for th in Theme
            ),
            bridges_required=_lerp_int(
                *p.bridge_required, t,
            ),
            bridges_provided=_lerp_int(
                *p.bridge_provided, t,
            ),
        ))
    return NarrativeTrajectory(
        firm_id=firm.firm_id,
        sector=firm.sector,
        post_hoc_label=firm.post_hoc_label,
        years=tuple(rows),
    )


_TRAJECTORIES: tuple[NarrativeTrajectory, ...] = tuple(
    _build(f) for f in firms()
)


def trajectories() -> tuple[NarrativeTrajectory, ...]:
    return _TRAJECTORIES


def by_id(firm_id: str) -> NarrativeTrajectory:
    for tr in _TRAJECTORIES:
        if tr.firm_id == firm_id:
            return tr
    raise KeyError(firm_id)


def years() -> tuple[int, ...]:
    return tuple(
        _START_YEAR + t for t in range(_N_YEARS)
    )


def claim_fulfilment(firm_id: str) -> float:
    return _TRAJ[firm_id].claim_fulfilment


def _weight_vec(
    y: NarrativeYear,
) -> dict[str, float]:
    return {k: v for k, v in y.theme_weights}


def narrative_drift_firm(
    tr: NarrativeTrajectory,
) -> float:
    """Cumulative distance the theme distribution
    has travelled from the first year to the last
    (half the L1 distance, in [0, 1]). High = the
    story has moved a long way from where it
    started - an audit-worthy re-telling, NOT a
    fraud claim."""
    if len(tr.years) < 2:
        return 0.0
    wa = _weight_vec(tr.years[0])
    wb = _weight_vec(tr.years[-1])
    l1 = sum(abs(wb[k] - wa[k]) for k in wa)
    return _round(0.5 * l1)


def narrative_drift() -> float:
    """Corpus mean of per-firm narrative drift."""
    trs = trajectories()
    if not trs:
        return 0.0
    vals = [narrative_drift_firm(t) for t in trs]
    return _round(sum(vals) / len(vals))


__all__ = [
    "THEMES",
    "NarrativeTrajectory",
    "NarrativeYear",
    "Theme",
    "by_id",
    "claim_fulfilment",
    "narrative_drift",
    "narrative_drift_firm",
    "trajectories",
    "years",
]
