"""Red-team benchmark: does a scientific "background reviewer" catch the five
epistemic failure modes the MarCognity / Muse Spark case study identified?

Motivated by Claude Science's "background reviewer [that] flags incorrect citations,
untraceable numbers, and figures that don't match their underlying code". The case
study becomes a probe set; any reviewer (the DESi reference, a naive whole-text
baseline, or an external reviewer's JSON output) is scored on catch-rate. The point
is DESi as a *counter-check and benchmark* for such reviewers, not a replacement.

Run: ``python -m desi.case_studies.marcognity_muse_spark.redteam``
"""
from __future__ import annotations

from . import bench, failure_modes, reviewers

__all__ = ["bench", "failure_modes", "reviewers"]
