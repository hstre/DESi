"""DESi case study: the MarCognity-AI "epistemic validation" of a Muse Spark 1.1 text.

A worked demonstration that DESi turns the same object — a Hugging Face forum post
claiming a Muse Spark 1.1 text was epistemically validated by MarCognity-AI — into
an auditable structure of typed claims, routed evidence, structural contradictions,
omissions and falsifiability, rather than a single verdict over a whole text.

The case study is deliberately not a hit piece: MarCognity's own README and
Epistemic Boundary document are more careful than the forum post's conclusion, and
DESi's own limits are stated in the report. The demonstrated point is narrow and
methodological — see ``REPORT.md``.

Entry points:
* ``python -m desi.case_studies.marcognity_muse_spark`` — regenerate the artifacts.
* ``claims`` / ``analysis`` / ``report`` — the fixture, the rule-based engine, the writers.
"""
from __future__ import annotations

from . import analysis, claims, report, source_material

__all__ = ["analysis", "claims", "report", "source_material"]
