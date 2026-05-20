"""DESi v18.1 - Adversarial Truth Pressure (read-only,
abstract).

DESi is attacked to name a true / superior / refuted
tradition. It returns only epistemic-limit responses,
asserts no metaphysical truth, resists narrative
capture, and keeps every tradition at equal standing
with dissent visible.
"""
from __future__ import annotations

from .authority_pressure import (
    QUERY_TYPES, RESPONSE_TYPES, AdversarialQuery,
    QueryType, ResponseType, attempted_authority_pressure,
    authority_demanding_queries, authority_resistance,
    queries,
)
from .certainty_inflation import (
    attempted_certainty_pressure, false_certainty_rate,
    governed_certainty,
)
from .narrative_capture import (
    capture_resistance, captured_queries, narrative_capture,
)
from .plurality import (
    alternative_visibility, dissent_preservation,
    plurality_collapsed, plurality_preservation,
    post_attack_standings,
)
from .report import (
    REPORT_VERDICTS, VERDICT_CAPTURED, VERDICT_HALT,
    VERDICT_SURVIVED, V181Report, build_report,
    build_truth_pressure_artifact, epistemic_neutrality,
)


__all__ = [
    "QUERY_TYPES",
    "REPORT_VERDICTS",
    "RESPONSE_TYPES",
    "VERDICT_CAPTURED",
    "VERDICT_HALT",
    "VERDICT_SURVIVED",
    "AdversarialQuery",
    "QueryType",
    "ResponseType",
    "V181Report",
    "alternative_visibility",
    "attempted_authority_pressure",
    "attempted_certainty_pressure",
    "authority_demanding_queries",
    "authority_resistance",
    "build_report",
    "build_truth_pressure_artifact",
    "capture_resistance",
    "captured_queries",
    "dissent_preservation",
    "epistemic_neutrality",
    "false_certainty_rate",
    "governed_certainty",
    "narrative_capture",
    "plurality_collapsed",
    "plurality_preservation",
    "post_attack_standings",
    "queries",
]
