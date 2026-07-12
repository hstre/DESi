"""Doktores audit of the DESi MarCognity / Muse Spark 1.1 case study.

A **rule-guided self-audit**: four source-anchored reviewer roles (provenance,
methodology, logic, fairness) try to refute, revise or bound the DESi findings. It
is **logically and provenance adversarial** but **not organizationally or model-side
independent** — all four reviewers are fixed rules from the same repository, so it is
a clean deterministic counter-check, NOT an independent replication (see
``engine.INDEPENDENCE_NOTE``). Offline, no LLM, qualitative confidence.

The result is deliberately mixed — some findings survive, some are qualified, two
"structural contradiction" labels are downgraded, dissent is preserved — and the
attestation certifies method, not the truth of the legal statements.

Run: ``python -m desi.case_studies.marcognity_muse_spark.doktores``
"""
from __future__ import annotations

from . import engine, models, reviews

__all__ = ["engine", "models", "reviews"]
