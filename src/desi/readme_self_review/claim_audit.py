"""README/System-Paper self-review - claim extraction + Concept Gate.

The Reviewer Port extracts the paper's load-bearing claims, assigns
each exactly one status from a closed enumeration, and records its
evidence source, artifact support, risk level and recommended action.
The seven Concept-Gate metrics are then derived from the classified
claims and the deterministic scanners.

This is a hard, skeptical audit: claims that this audit cannot trace
to a committed artifact are marked NEEDS_ARTIFACT_CHECK (not assumed
supported); internal inconsistencies and grandiose framing are marked
as overreach. The audit does not confer authority on the document.
"""
from __future__ import annotations

from dataclasses import dataclass

from .reviewer_port import (
    builtin_hash_pattern_hits, compression_range_consistent,
    external_generalization_guard_present, forbidden_term_hits,
    replay_explanation_present, reviewer_port_module_present,
    stale_regression_runs, synthetic_real_separation_present,
)

# Closed status enumeration (directive Pflichtklassifikation).
STATUS_SUPPORTED = "SUPPORTED"
STATUS_SCOPE_LIMIT = "SUPPORTED_WITH_SCOPE_LIMIT"
STATUS_NEEDS_CHECK = "NEEDS_ARTIFACT_CHECK"
STATUS_OVERSTATED = "OVERSTATED"
STATUS_UNSUPPORTED = "UNSUPPORTED"
STATUS_HYPE_RISK = "FORBIDDEN_OR_HYPE_RISK"
STATUS_EXTERNAL = "EXTERNAL_VALIDATION_REQUIRED"

CLAIM_STATUSES: tuple[str, ...] = (
    STATUS_SUPPORTED, STATUS_SCOPE_LIMIT, STATUS_NEEDS_CHECK,
    STATUS_OVERSTATED, STATUS_UNSUPPORTED, STATUS_HYPE_RISK,
    STATUS_EXTERNAL,
)

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claim_text: str
    claim_type: str
    evidence_source: str
    artifact_support: str
    risk_level: str
    verdict: str
    recommended_action: str
    numeric: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "evidence_source": self.evidence_source,
            "artifact_support": self.artifact_support,
            "risk_level": self.risk_level,
            "verdict": self.verdict,
            "recommended_action": self.recommended_action,
            "numeric": self.numeric,
        }


def _claims() -> tuple[Claim, ...]:
    return (
        # --- backed by this session's artifacts (v28-v38) ---
        Claim("RM-01",
              "Recompute reduction from 36 to 4 operations (88.9%) "
              "under the frozen longitudinal benchmark with "
              "byte-identical outputs (v32).",
              "metric", "abstract / §5.4",
              "artifacts/frozen_benchmark/v32_4_verdict.json "
              "(measured_improvement=0.889)",
              RISK_LOW, STATUS_SUPPORTED,
              "Keep; already scope-limited to the frozen workload.",
              True),
        Claim("RM-02",
              "Real external benchmark node_reduction = 41.7% with "
              "critical_branch_preservation = 1.0 (v35.2).",
              "metric", "§6.3 / §9.3",
              "artifacts/external_benchmarks/v35_2_real_search.json "
              "(node_reduction=0.4167)",
              RISK_LOW, STATUS_SUPPORTED, "Keep.", True),
        Claim("RM-03",
              "hallucination_containment = 1.0 under live OpenRouter "
              "calls (v38).",
              "metric", "abstract / §7.2",
              "artifacts/live_llm_validation/v38_4_verdict.json; the "
              "metric is visibility-based, not absence of "
              "hallucination",
              RISK_HIGH, STATUS_SCOPE_LIMIT,
              "Carry the §2.3/§7.2 caveat ('visibility, not "
              "absence') INTO the abstract; the bare phrase "
              "'containment at 1.0' reads as 'no hallucinations', "
              "which is false.",
              True),
        Claim("RM-04",
              "Routing cost reduction of 53.5% with quality "
              "preservation at 1.0 (v38.3).",
              "metric", "abstract / §7.2 / §12",
              "artifacts/live_llm_validation/v38_3_routing.json: "
              "53.5% is the mean per-task saving; total-workload "
              "saving is 7.3%",
              RISK_MEDIUM, STATUS_SCOPE_LIMIT,
              "State alongside 53.5% the total-workload figure "
              "(7.3%) and routed-down efficiency (98.6%); the "
              "headline alone is favourable-framing.",
              True),
        Claim("RM-05",
              "The system identified one overengineered component "
              "(neo4j_evolution_graph, efficiency = -0.5).",
              "limitation", "§5.4 / §10",
              "artifacts/frozen_benchmark/v32_3_utility.json",
              RISK_LOW, STATUS_SUPPORTED,
              "Keep; this honest negative result is a strength.",
              True),
        Claim("RM-06",
              "core_identity = 1.0 and replay_stability = 1.0 "
              "maintained across the evolution and live phases.",
              "metric", "§5.3 / §7 / Appendix B",
              "v31/v32/v38 verdict artifacts (core_identity=1.0, "
              "replay_stability=1.0)",
              RISK_LOW, STATUS_SCOPE_LIMIT,
              "Scope explicitly to v28-v38 (this audit verified "
              "those); state v1-v27 separately.",
              False),
        # --- structural strengths ---
        Claim("ST-01",
              "All results are derived from synthetic or locally "
              "vendored fixtures unless explicitly noted; v38 is the "
              "only phase with real API calls.",
              "safety_governance", "abstract / §6.2 / §7 / §9.1",
              "consistent across the paper; v38 separated cleanly",
              RISK_LOW, STATUS_SUPPORTED,
              "Keep; clean synthetic-vs-real separation.", False),
        Claim("ST-02",
              "Explicit non-generalization guards: results do not "
              "generalize to production LLM workloads; the §9.3 "
              "extrapolation is 'an engineering implication, not a "
              "measured result'.",
              "production_generalization", "§9.2 / §9.3 / §10",
              "guard present and explicit",
              RISK_LOW, STATUS_SUPPORTED,
              "Keep; strong guard. Watch §9.3 superlinear-savings "
              "extrapolation - keep it clearly labelled.", False),
        Claim("ST-03",
              "Replay stability is explained correctly (bit-exact, "
              "hashlib.sha256, no PRNG; deterministic projection "
              "over a stochastic proposal operator).",
              "reproducibility", "§1 / §2.3 / Appendix B / Appendix C",
              "explanation correct and thorough",
              RISK_LOW, STATUS_SUPPORTED, "Keep.", False),
        Claim("ST-04",
              "Replay stability is a property of DESi, not of the "
              "LLMs it governs; LLM stochasticity is observed, not "
              "eliminated.",
              "limitation", "§10",
              "limitation stated explicitly",
              RISK_LOW, STATUS_SUPPORTED, "Keep.", False),
        Claim("ST-05",
              "LangGraph is treated as an optional execution "
              "substrate, not a foundation ('DESi is "
              "execution-framework agnostic').",
              "production_generalization", "§11.2",
              "framing correct; but 'frequently introduces agentic "
              "drift / hidden state' is an unsupported empirical "
              "sub-claim about LangGraph",
              RISK_MEDIUM, STATUS_SCOPE_LIMIT,
              "Keep the 'optional substrate' framing; soften or cite "
              "the unsupported claim that LangGraph 'frequently' "
              "introduces drift.", False),
        Claim("ST-06",
              "Limitations section enumerates synthetic fixtures, "
              "minimal live validation, no peer review, the "
              "overengineered neo4j component, two sub-ceiling gate "
              "scores, replay != LLM stability, and 362 ungrounded "
              "tokens.",
              "limitation", "§10",
              "limitations broad and visible",
              RISK_LOW, STATUS_SUPPORTED,
              "Keep; add the open v1-v27 artifact-traceability "
              "caveat (see NC-* claims).", False),
        # --- v1-v27 numerics not verifiable in this audit ---
        Claim("NC-01",
              "Failure-taxonomy results (Table 2): precision "
              "0.5->1.0, gate-ablation trajectory AUC 0.283, "
              "228/250 trajectories rescued, 36/52 unrecoverable "
              "pools, replay hash 1f4d9dfe44cb16e1.",
              "metric", "§3 Table 2",
              "v1-v22 base-system artifacts NOT verified in this "
              "audit round",
              RISK_MEDIUM, STATUS_NEEDS_CHECK,
              "Cross-check each value against its v1-v22 artifact "
              "JSON before public release; cite the artifact path "
              "per row.",
              True),
        Claim("NC-02",
              "Canonical result values (§3.1): redundancy_reduction "
              "0.900, productivity_gain 2.750, etc.",
              "metric", "§3.1",
              "v19-v21 artifacts NOT verified in this audit round",
              RISK_MEDIUM, STATUS_NEEDS_CHECK,
              "Verify against v19-v21 artifacts; add per-value "
              "source paths.", True),
        Claim("NC-03",
              "v11.1 chess search 53.3% and v15.3 financial audit "
              "60.4% node/search reduction with critical "
              "preservation 1.0 (§9.3 four-context table).",
              "metric", "§9.3",
              "v11.1/v15.3 artifacts NOT verified in this audit "
              "round (v35.2 and v38.3 ARE verified)",
              RISK_MEDIUM, STATUS_NEEDS_CHECK,
              "Verify v11.1/v15.3 artifacts; otherwise scope the "
              "41-60% range to the two verified contexts.", True),
        Claim("NC-04",
              "All 17 domains (v6-v22) achieved Class A with "
              "six-condition Concept Gate passage.",
              "metric", "§3.2 / Table 1 / Appendix A",
              "v6-v22 verdict artifacts NOT verified in this audit "
              "round",
              RISK_MEDIUM, STATUS_NEEDS_CHECK,
              "Verify each verdict artifact; an all-Class-A table "
              "invites reviewer scepticism - cite sources.", False),
        # --- internal inconsistency / staleness ---
        Claim("IN-01",
              "Headline search-compression range is stated "
              "inconsistently: '41-60%' (abstract/§9.3), '~42-50%' "
              "(§9.1), '~42%' (§12).",
              "metric", "abstract / §9.1 / §9.3 / §12",
              "internal inconsistency detected by the consistency "
              "scanner",
              RISK_MEDIUM, STATUS_OVERSTATED,
              "Pick ONE range (the verified contexts give 41.7-60.4%)"
              " and use it consistently everywhere.", True),
        Claim("IN-02",
              "The regression-milestones table (§8) ends at v27 "
              "(7,204 passed) and omits the committed v31 (7,573) "
              "and v32 (7,683) full-regression runs.",
              "metric", "§8",
              "contradicted by committed "
              "_regression_status.json artifacts (v31=7573, "
              "v32=7683)",
              RISK_MEDIUM, STATUS_UNSUPPORTED,
              "Update §8 with the v31/v32 (and later) full "
              "regressions, or scope the table to 'through v27'.",
              True),
        # --- grandiose framing / hype risk ---
        Claim("HY-01",
              "'DESi ... is a different category of system entirely "
              "- an epistemic operating system with its own "
              "ontology.'",
              "overreach", "§1",
              "metaphor; not falsifiable; grandiose framing",
              RISK_HIGH, STATUS_HYPE_RISK,
              "Demote 'epistemic operating system' to a descriptive "
              "phrase or remove; it reads as marketing and is not a "
              "testable claim.", False),
        Claim("HY-02",
              "'Epistemic cartography and the map of unknown "
              "unknowns' (§9.5).",
              "overreach", "§9.5",
              "'mapping unknown unknowns' is self-undermining by "
              "definition; the section partly hedges",
              RISK_HIGH, STATUS_OVERSTATED,
              "Rename to what is actually done (marking interrupted/"
              "compressed/blinded exploration); drop 'map of unknown "
              "unknowns'.", False),
        Claim("HY-03",
              "'At the heart of DESi lies the Reviewer Port ... "
              "epistemic topology analysis ... native "
              "meta-governance.'",
              "overreach", "§11.3",
              "no src/desi/reviewer_port.py module exists; the "
              "capability maps to scientific_reviewers / output "
              "ports / the SKEPTICAL_AUDITOR role",
              RISK_MEDIUM, STATUS_SCOPE_LIMIT,
              "Name the actual modules that implement the Reviewer "
              "Port; soften 'epistemic topology analysis' to its "
              "concrete operations.", False),
        Claim("HY-04",
              "'External runtime-oriented tools such as LangSmith "
              "are consequently largely unnecessary ... and "
              "potentially counterproductive.'",
              "production_generalization", "§11.3",
              "comparative dismissal of an external tool with no "
              "comparative experiment",
              RISK_HIGH, STATUS_EXTERNAL,
              "Remove or reframe as 'DESi's replay-bound capture "
              "reduces reliance on external runtime tracing'; do not "
              "assert another tool is counterproductive without "
              "evidence.", False),
        Claim("SC-01",
              "The README itself contains all 11 forbidden terms "
              "(§2.2 governance listing) and would therefore trip "
              "DESi's own forbidden-term Determinism Scanner.",
              "safety_governance", "§2.2",
              "forbidden_term scanner returns 11 hits on the README",
              RISK_HIGH, STATUS_HYPE_RISK,
              "This is documentation, not a rendered output, so it "
              "is acceptable for humans - but note explicitly that "
              "the README is exempt from the rendered-output scanner,"
              " or move the term listing to a code constant / "
              "appendix the scanner whitelists.", False),
    )


def claims() -> tuple[Claim, ...]:
    return _claims()


def claims_by_status() -> dict[str, int]:
    out = {s: 0 for s in CLAIM_STATUSES}
    for c in claims():
        out[c.verdict] += 1
    return out


# --- the seven Concept-Gate metrics -------------
def _numeric_claims() -> tuple[Claim, ...]:
    return tuple(c for c in claims() if c.numeric)


def unsupported_numeric_claims() -> int:
    return sum(
        1 for c in _numeric_claims()
        if c.verdict in (STATUS_UNSUPPORTED, STATUS_OVERSTATED)
    )


def _needs_backing() -> tuple[Claim, ...]:
    # framing/safety claims are not artifact-backed by nature; the
    # backing rate is computed over claims that assert evidence
    return tuple(
        c for c in claims()
        if c.claim_type in (
            "metric", "reproducibility", "limitation",
        )
    )


def artifact_backing_rate() -> float:
    needing = _needs_backing()
    if not needing:
        return 0.0
    backed = sum(
        1 for c in needing
        if c.verdict in (STATUS_SUPPORTED, STATUS_SCOPE_LIMIT)
    )
    return round(backed / len(needing), 6)


def overreach_claims() -> int:
    return sum(
        1 for c in claims()
        if c.verdict in (STATUS_OVERSTATED, STATUS_HYPE_RISK)
    )


def forbidden_term_risk() -> int:
    return len(forbidden_term_hits())


def synthetic_vs_real_separation() -> float:
    return 1.0 if synthetic_real_separation_present() else 0.0


def external_generalization_guard() -> float:
    return 1.0 if external_generalization_guard_present() else 0.0


def replay_explanation_correct() -> float:
    return 1.0 if replay_explanation_present() else 0.0


@dataclass(frozen=True)
class GateCondition:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "passed": self.passed,
        }


def gate_conditions() -> tuple[GateCondition, ...]:
    return (
        GateCondition("unsupported_numeric_claims",
                      float(unsupported_numeric_claims()), 0.0, "==",
                      unsupported_numeric_claims() == 0),
        GateCondition("artifact_backing_rate",
                      artifact_backing_rate(), 0.95, ">=",
                      artifact_backing_rate() >= 0.95),
        GateCondition("overreach_claims",
                      float(overreach_claims()), 3.0, "<=",
                      overreach_claims() <= 3),
        GateCondition("forbidden_term_risk",
                      float(forbidden_term_risk()), 0.0, "==",
                      forbidden_term_risk() == 0),
        GateCondition("synthetic_vs_real_separation",
                      synthetic_vs_real_separation(), 1.0, "==",
                      synthetic_vs_real_separation() == 1.0),
        GateCondition("external_generalization_guard",
                      external_generalization_guard(), 1.0, "==",
                      external_generalization_guard() == 1.0),
        GateCondition("replay_explanation_correct",
                      replay_explanation_correct(), 1.0, "==",
                      replay_explanation_correct() == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(c.name for c in gate_conditions() if not c.passed)


def gate_passing_conditions() -> tuple[str, ...]:
    return tuple(c.name for c in gate_conditions() if c.passed)


__all__ = [
    "CLAIM_STATUSES",
    "Claim",
    "GateCondition",
    "STATUS_EXTERNAL",
    "STATUS_HYPE_RISK",
    "STATUS_NEEDS_CHECK",
    "STATUS_OVERSTATED",
    "STATUS_SCOPE_LIMIT",
    "STATUS_SUPPORTED",
    "STATUS_UNSUPPORTED",
    "artifact_backing_rate",
    "claims",
    "claims_by_status",
    "external_generalization_guard",
    "forbidden_term_risk",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "gate_passing_conditions",
    "overreach_claims",
    "replay_explanation_correct",
    "synthetic_vs_real_separation",
    "unsupported_numeric_claims",
]
