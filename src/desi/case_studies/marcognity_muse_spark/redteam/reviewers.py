"""Reviewers under test — a pluggable interface so any reviewer can be scored.

- ``DesiReviewer`` — the reference: content-scoped rules derive each flag from the
  parent case study's own analysis. It catches all five and raises no false
  positives **by construction** (it is the analysis that defined the probes), so
  BOTH its catch and its FP are reference properties, not independent achievements.
- ``NaiveWholeTextReviewer`` — models a coherence-first, whole-text reviewer (what
  MarCognity's Skeptical Agent effectively did): emits no flags.
- ``ExternalReviewer`` — loads a real reviewer's structured output from JSON,
  optionally across repeated runs (for stability), plus a cost/compute profile.

The point of the harness is the LAST one: score a real background reviewer (e.g.
Claude Science, a frontier LLM) on catch-rate, false positives, stability and cost —
that is where an interesting finding could live, not in the reference's own score.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from .. import analysis, claims as PC
from ..claims import ClaimType, ProvenanceKind, Verdict
from .failure_modes import Flag, Probe

_SELF_SEALING_CLAIMS = frozenset({"EB-01", "EB-02"})


@runtime_checkable
class Reviewer(Protocol):
    name: str

    def review(self, probe: Probe) -> set[Flag]:
        """Flags this reviewer raises for one probe (its representative run)."""
        ...

    def runs_for(self, probe: Probe) -> list[set[Flag]]:
        """One entry per repeated run (for stability). Default: a single run."""
        ...

    def profile(self) -> dict:
        """Cost / determinism metadata for the scorecard."""
        ...


class DesiReviewer:
    """Reference reviewer: content-scoped flags derived from the DESi analysis."""

    name = "desi"

    def review(self, probe: Probe) -> set[Flag]:
        raised: set[Flag] = set()
        by_id = PC.claims_by_id()
        cids = probe.claim_ids

        for cid in cids:
            v = by_id.get(cid)
            if not v:
                continue
            # untraceable citation — the verdict that specifically means "citation problem"
            if v.verdict == Verdict.CITATION_MISMATCH:
                raised.add(Flag.UNTRACEABLE_CITATION)
            # source-domain mismatch — the verdict, or the domain gate rejecting a
            # semantic-only source
            gate = analysis.source_domain_gate(cid)
            if v.verdict == Verdict.SOURCE_DOMAIN_MISMATCH or \
                    (not gate.admissible and gate.provenance_kind == ProvenanceKind.SEMANTIC_ONLY):
                raised.add(Flag.SOURCE_DOMAIN_MISMATCH)
            # overclaim
            if v.verdict == Verdict.UNSUPPORTED:
                raised.add(Flag.OVERCLAIM)
            # heuristic-as-measurement
            if v.claim_type == ClaimType.HEURISTIC_MODEL or v.verdict == Verdict.HEURISTIC_PROPOSAL:
                raised.add(Flag.HEURISTIC_NOT_EMPIRICAL)

        # self-sealing is a property of the conclusion — only for conclusion-linked probes
        if set(cids) & _SELF_SEALING_CLAIMS:
            ss = analysis.self_sealing_analysis()
            if ss.is_self_sealing and not ss.falsifiers_stated_in_experiment:
                raised.add(Flag.SELF_SEALING)
        return raised

    def runs_for(self, probe: Probe) -> list[set[Flag]]:
        return [self.review(probe)]                      # deterministic → one run suffices

    def profile(self) -> dict:
        return {"deterministic": True, "runs": 1,
                "compute": "cpu, offline, rule evaluation",
                "cost": "negligible (no model call)"}


class NaiveWholeTextReviewer:
    """Coherence-first whole-text reviewer — emits no epistemic flags (models MarCognity)."""

    name = "naive_whole_text"

    def review(self, probe: Probe) -> set[Flag]:
        return set()

    def runs_for(self, probe: Probe) -> list[set[Flag]]:
        return [set()]

    def profile(self) -> dict:
        return {"deterministic": True, "runs": 1,
                "compute": "modelled (one whole-text LLM verdict)",
                "cost": "high in reality (1 LLM pass); stubbed here"}


class ExternalReviewer:
    """Scores a real reviewer's structured output, loaded from JSON.

    JSON shape (single run)::
        {"name": "...", "flags": {"P2-domain": ["source_domain_mismatch"], ...},
         "profile": {"cost": "...", "compute": "..."}}

    Or with repeated runs for stability::
        {"name": "...", "runs": [ {"P2-domain": ["source_domain_mismatch"]}, {...} ],
         "profile": {...}}

    Unknown flag strings are ignored. This is how a real background reviewer (Claude
    Science, a frontier LLM) gets red-teamed on the same probes without live access.
    """

    def __init__(self, name: str, runs: list[dict[str, set[Flag]]], profile: dict):
        self.name = name
        self._runs = runs or [{}]
        self._profile = profile

    def _run(self, i: int, probe: Probe) -> set[Flag]:
        return set(self._runs[i].get(probe.key, set()))

    def review(self, probe: Probe) -> set[Flag]:
        return self._run(0, probe)                        # representative (first) run

    def runs_for(self, probe: Probe) -> list[set[Flag]]:
        return [self._run(i, probe) for i in range(len(self._runs))]

    def profile(self) -> dict:
        return {"deterministic": len(self._runs) <= 1, "runs": len(self._runs),
                **self._profile}

    @classmethod
    def from_json(cls, path: str | Path) -> "ExternalReviewer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        known = {f.value: f for f in Flag}

        def parse(m: dict) -> dict[str, set[Flag]]:
            return {k: {known[s] for s in v if s in known} for k, v in (m or {}).items()}

        if "runs" in data:
            runs = [parse(r) for r in data["runs"]]
        else:
            runs = [parse(data.get("flags") or {})]
        return cls(data.get("name", "external"), runs, data.get("profile") or {})


def default_reviewers() -> list[Reviewer]:
    return [DesiReviewer(), NaiveWholeTextReviewer()]


__all__ = [
    "Reviewer", "DesiReviewer", "NaiveWholeTextReviewer", "ExternalReviewer",
    "default_reviewers",
]
