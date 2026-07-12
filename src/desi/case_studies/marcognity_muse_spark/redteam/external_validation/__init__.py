"""External-validation tooling for the frozen R1 v2 rule (PMC OA / Europe PMC).

Four building blocks, per the pre-registered protocol (EXTERNAL_VALIDATION_PROTOCOL.md):
  - ``europepmc``  : search the PMC OA subset + fetch JATS full-text XML
  - ``jats``       : parse JATS into sections/paragraphs/sentences/tables (frozen splitter)
  - ``candidates`` : stratified candidate-claim generation (p / CI / effect-size / relevance)
  - ``export``     : blind annotation workbook + document manifest

This tooling ONLY prepares candidates and a blind annotation export. It does not touch
v2, does not run the rule, and does not produce gold labels — annotators do that.
"""
from __future__ import annotations

from . import candidates, europepmc, export, jats

__all__ = ["europepmc", "jats", "candidates", "export"]
