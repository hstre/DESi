"""Reviewers under test — a pluggable interface so any reviewer can be scored.

- ``DesiReviewer`` — the reference: it derives each flag DETERMINISTICALLY from the
  parent case study's own analysis (source-domain gate, self-sealing check, claim
  types/verdicts). It catches all five **by construction** — it IS the analysis that
  defined the probes — so it is a gold/reference reviewer, not an independent
  achievement. Its role is to anchor the benchmark and show the flags are derivable
  from rules, not vibes.
- ``NaiveWholeTextReviewer`` — models a coherence-first, whole-text reviewer (what
  MarCognity's Skeptical Agent effectively did): it emits no flags. It exists so the
  benchmark demonstrably DISCRIMINATES (a reviewer can score 0).
- ``ExternalReviewer`` — loads a real reviewer's structured output from JSON, so you
  can score an external background reviewer (e.g. a transcript of its findings)
  without live access.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from .. import analysis, claims as PC
from ..claims import ClaimType, ProvenanceKind, Verdict
from .failure_modes import PROBES, Flag, Probe


@runtime_checkable
class Reviewer(Protocol):
    name: str

    def review(self, probe: Probe) -> set[Flag]:
        """Return the set of flags this reviewer raises for one probe."""
        ...


class DesiReviewer:
    """Reference reviewer: flags derived deterministically from the DESi analysis."""

    name = "desi"

    def review(self, probe: Probe) -> set[Flag]:
        raised: set[Flag] = set()
        by_id = PC.claims_by_id()
        ev = PC.evidence_by_id()

        # P1 — untraceable citation: a "verified"/asserted claim whose evidence names
        # no source or passage (provenance none/semantic, empty passage).
        for cid in probe.claim_ids:
            e = ev.get(cid)
            if e and e.provenance_kind in (ProvenanceKind.NONE, ProvenanceKind.SEMANTIC_ONLY) \
                    and not e.concrete_passage.strip():
                raised.add(Flag.UNTRACEABLE_CITATION)
            v = by_id.get(cid)
            if v and v.verdict in (Verdict.CITATION_MISMATCH, Verdict.SOURCE_DOMAIN_MISMATCH):
                raised.add(Flag.UNTRACEABLE_CITATION)

        # P2 — source-domain mismatch: the gate rejects the used source's domain.
        for cid in probe.claim_ids:
            gate = analysis.source_domain_gate(cid)
            if not gate.admissible and gate.provenance_kind == ProvenanceKind.SEMANTIC_ONLY:
                raised.add(Flag.SOURCE_DOMAIN_MISMATCH)
            if by_id.get(cid) and by_id[cid].verdict == Verdict.SOURCE_DOMAIN_MISMATCH:
                raised.add(Flag.SOURCE_DOMAIN_MISMATCH)

        # P3 — self-sealing: the deterministic falsifiability check fires.
        ss = analysis.self_sealing_analysis()
        if ss.is_self_sealing and not ss.falsifiers_stated_in_experiment:
            raised.add(Flag.SELF_SEALING)

        # P4 — overclaim: an EB claim judged unsupported (reach beyond the evidence).
        for cid in probe.claim_ids:
            if by_id.get(cid) and by_id[cid].verdict == Verdict.UNSUPPORTED:
                raised.add(Flag.OVERCLAIM)

        # P5 — heuristic-not-empirical: a heuristic-model claim / heuristic_proposal verdict.
        for cid in probe.claim_ids:
            v = by_id.get(cid)
            if v and (v.claim_type == ClaimType.HEURISTIC_MODEL
                      or v.verdict == Verdict.HEURISTIC_PROPOSAL):
                raised.add(Flag.HEURISTIC_NOT_EMPIRICAL)

        # Only credit flags relevant to THIS probe's failure mode (the benchmark scores
        # per-mode); cross-mode signals are dropped so a probe isn't "caught" by accident.
        return {f for f in raised if f == probe.must_flag}


class NaiveWholeTextReviewer:
    """Coherence-first whole-text reviewer — emits no epistemic flags (models MarCognity)."""

    name = "naive_whole_text"

    def review(self, probe: Probe) -> set[Flag]:
        return set()


class ExternalReviewer:
    """Scores a real reviewer's structured output, loaded from JSON.

    JSON shape: ``{"name": "...", "flags": {"<probe_key>": ["untraceable_citation", ...]}}``.
    Unknown flag strings are ignored (with the benefit of the doubt going to the
    reviewer only if the string matches a known Flag).
    """

    def __init__(self, name: str, flags: dict[str, set[Flag]]):
        self.name = name
        self._flags = flags

    def review(self, probe: Probe) -> set[Flag]:
        return {f for f in self._flags.get(probe.key, set()) if f == probe.must_flag}

    @classmethod
    def from_json(cls, path: str | Path) -> "ExternalReviewer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        known = {f.value: f for f in Flag}
        flags: dict[str, set[Flag]] = {}
        for key, raw in (data.get("flags") or {}).items():
            flags[key] = {known[s] for s in raw if s in known}
        return cls(data.get("name", "external"), flags)


def default_reviewers() -> list[Reviewer]:
    return [DesiReviewer(), NaiveWholeTextReviewer()]


# sanity: every probe's must_flag is a real Flag the DesiReviewer can emit
assert all(p.must_flag in set(Flag) for p in PROBES)

__all__ = [
    "Reviewer", "DesiReviewer", "NaiveWholeTextReviewer", "ExternalReviewer",
    "default_reviewers",
]
