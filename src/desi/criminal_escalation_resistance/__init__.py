"""DESi v16.2 - Conspiracy Escalation Resistance
(Kennedy epistemics sandbox, read-only).

Stress-tests DESi against chains of conjecture,
unsupported causal jumps, confidence inflation, and
hidden assumptions. DESi caps every node at its
evidence grade, surfaces hidden assumptions, keeps
dissent visible, and never tips into conspiracy
dynamics. Makes no new factual claim.
"""
from __future__ import annotations

from .confidence_control import (
    attempted_pressure, false_certainty_rate,
    speculation_growth,
)
from .escalation import (
    CHAIN_IDS, ChainId, EscalationChain,
    EscalationNode, attempted_escalations, chains,
    escalation_resistance, flagged_escalations, nodes,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_LEAK,
    VERDICT_RESISTED, V162Report,
    build_escalation_artifact, build_report,
    epistemic_integrity,
)
from .speculation_tracking import (
    all_chains_visible, chain_lengths,
    speculation_chains, visible_escalation_count,
)
from .uncertainty_governance import (
    detected_hidden_assumptions, dissent_preservation,
    dissent_targets, hidden_assumption_detection,
    hidden_assumptions,
)


__all__ = [
    "CHAIN_IDS",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_LEAK",
    "VERDICT_RESISTED",
    "ChainId",
    "EscalationChain",
    "EscalationNode",
    "V162Report",
    "all_chains_visible",
    "attempted_escalations",
    "attempted_pressure",
    "build_escalation_artifact",
    "build_report",
    "chain_lengths",
    "chains",
    "detected_hidden_assumptions",
    "dissent_preservation",
    "dissent_targets",
    "epistemic_integrity",
    "escalation_resistance",
    "false_certainty_rate",
    "flagged_escalations",
    "hidden_assumption_detection",
    "hidden_assumptions",
    "nodes",
    "speculation_chains",
    "speculation_growth",
    "visible_escalation_count",
]
