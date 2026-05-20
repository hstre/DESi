"""Showcase package — externally-readable demonstration runs.

v0.4.1 takes three already-validated scenarios (S2, S6, S7) and turns
each one into a reproducible bundle of artefacts a reviewer can read
without running the code:

* ``summary.json``        — eval id, scenario id, seed, model, hash, pass/fail map
* ``timeline.md``         — the timeline as a markdown table
* ``timeline.json``       — same timeline, JSON
* ``snapshot_start.json`` — graph state at run start
* ``snapshot_end.json``   — graph state at run end
* ``snapshot_end.cypher`` — same end-state as Neo4j-importable Cypher
* ``analysis.md``         — human-readable analysis (Problem / Verhalten /
                            Endzustand / Warum relevant)

Plus one top-level ``baseline_notes.md`` that contrasts each showcase
with what a classical LLM run would typically hide.

Design contract: the runner is observation-only. It re-uses the v0.4
EvaluationHarness without modification. No new operators, no memory
reads, no behaviour change.
"""
from __future__ import annotations

from .descriptions import SHOWCASE_DESCRIPTIONS, SHOWCASE_IDS
from .runner import ShowcaseRunner, ShowcaseArtifacts

__all__ = [
    "SHOWCASE_DESCRIPTIONS",
    "SHOWCASE_IDS",
    "ShowcaseArtifacts",
    "ShowcaseRunner",
]
