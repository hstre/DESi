"""Adversarial Doktores audit of the DESi MarCognity / Muse Spark 1.1 case study.

Four source-anchored reviewer roles (provenance, methodology, logic, fairness) try
to refute, revise or bound the DESi findings. Deterministic and offline: no LLM is
called, confidence is qualitative. The result is deliberately mixed — some findings
survive, some are qualified, two "structural contradiction" labels are downgraded,
and dissent is preserved. The attestation certifies method, not the truth of the
legal statements.

Run: ``python -m desi.case_studies.marcognity_muse_spark.doktores``
"""
from __future__ import annotations

from . import engine, models, reviews

__all__ = ["engine", "models", "reviews"]
