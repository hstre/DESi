"""README/System-Paper self-review - artifact builders.

Emits the four required deliverables:

* desi_readme_claim_audit.json       - full claim audit + Concept Gate
* desi_readme_overreach_report.md    - overreach / hype / scanner risks
* desi_readme_revision_suggestions.md- concrete recommended actions
* desi_readme_go_no_go.md            - the gate verdict

Safety rule (directive): this is an INTERNAL CONSISTENCY AND OVERREACH
AUDIT of DESi's own documentation. The artifacts never assert that
"DESi validates itself". The honest outcome of a hard audit may be -
and here is - NO-GO pending revisions.
"""
from __future__ import annotations

import hashlib
import json

from .claim_audit import (
    STATUS_EXTERNAL, STATUS_HYPE_RISK, STATUS_OVERSTATED,
    STATUS_UNSUPPORTED, artifact_backing_rate, claims,
    claims_by_status, forbidden_term_risk, gate_conditions,
    gate_failing_conditions, gate_passes_all, gate_passing_conditions,
    overreach_claims, unsupported_numeric_claims,
)
from .reviewer_port import (
    AUDIT_FRAMING, compression_range_phrasings, forbidden_term_hits,
    reviewed_hash, reviewer_port_module_present, stale_regression_runs,
)

VERDICT_PUBLIC_READY = "README_PUBLIC_FACING_READY_WITH_SCOPE_LIMITS"
VERDICT_NOT_READY = "README_NOT_FINAL_PUBLIC_FACING_REVISIONS_REQUIRED"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PUBLIC_READY, VERDICT_NOT_READY,
)

_DOC_TITLE = "DESi System Paper v1.1 (README on main)"


def recommendation() -> str:
    return (
        VERDICT_PUBLIC_READY if gate_passes_all()
        else VERDICT_NOT_READY
    )


def _flagged() -> tuple:
    flag = {
        STATUS_OVERSTATED, STATUS_UNSUPPORTED, STATUS_HYPE_RISK,
        STATUS_EXTERNAL,
    }
    return tuple(c for c in claims() if c.verdict in flag)


def build_claim_audit_artifact() -> dict[str, object]:
    return {
        "schema_version": "readme_self_review_claim_audit",
        "audit_framing": AUDIT_FRAMING,
        "disclaimer": (
            "Internal consistency and overreach audit of DESi's own "
            "documentation, performed by the Reviewer Port against a "
            "fixed snapshot of the README (System Paper v1.1). This "
            "is NOT self-validation: the README is treated as an "
            "external claim artifact, and DESi confers no authority "
            "on it. Claims this audit could not trace to a committed "
            "artifact are marked NEEDS_ARTIFACT_CHECK rather than "
            "assumed supported. The outcome of this hard audit is a "
            "NO-GO pending revisions."
        ),
        "reviewed_document": _DOC_TITLE,
        "reviewed_snapshot_sha256": reviewed_hash(),
        "report_verdicts": list(REPORT_VERDICTS),
        "claim_statuses_used": dict(claims_by_status()),
        "claims": [c.to_dict() for c in claims()],
        "gate_conditions": [c.to_dict() for c in gate_conditions()],
        "gate_passes_all": gate_passes_all(),
        "gate_failing_conditions": list(gate_failing_conditions()),
        "gate_passing_conditions": list(gate_passing_conditions()),
        "scanner_facts": {
            "forbidden_term_hits": list(forbidden_term_hits()),
            "compression_range_phrasings":
                compression_range_phrasings(),
            "stale_regression_runs_omitted_by_readme":
                list(stale_regression_runs()),
            "reviewer_port_module_present":
                reviewer_port_module_present(),
        },
        "recommendation": recommendation(),
    }


def build_overreach_report() -> str:
    lines = [
        "# DESi README/Paper Self-Review - Overreach & Scanner Report",
        "",
        f"_{AUDIT_FRAMING}_",
        "",
        f"**Reviewed:** {_DOC_TITLE} (snapshot sha256 "
        f"`{reviewed_hash()[:16]}`)",
        "",
        f"**Overreach/hype claims:** {overreach_claims()} "
        f"(gate floor: <= 3).",
        f"**Forbidden-term scanner hits in the README:** "
        f"{forbidden_term_risk()} - {list(forbidden_term_hits())}.",
        "",
        "## Flagged claims (overreach / unsupported / hype / "
        "external-validation)",
        "",
    ]
    for c in _flagged():
        lines += [
            f"### {c.claim_id} - {c.verdict} ({c.risk_level} risk)",
            f"- **Claim:** {c.claim_text}",
            f"- **Type / source:** {c.claim_type} / "
            f"{c.evidence_source}",
            f"- **Why flagged:** {c.artifact_support}",
            f"- **Action:** {c.recommended_action}",
            "",
        ]
    lines += [
        "## Structural strengths (credited, not overreach)",
        "",
        "- Synthetic-vs-real separation is clean and explicit "
        "(abstract, §6.2, §7, §9.1).",
        "- Non-generalization guards are strong (§9.2 'What the "
        "Results Do Not Support'; §9.3 extrapolation labelled 'not a "
        "measured result').",
        "- Replay stability is explained correctly (§1, §2.3, "
        "Appendices B & C).",
        "- The paper reports its own overengineered component "
        "(neo4j) and two sub-ceiling gate scores - honest negatives.",
        "",
        "## Scanner & consistency findings",
        "",
        f"- The README would trip DESi's forbidden-term scanner on "
        f"all {forbidden_term_risk()} terms (§2.2 lists them). It is "
        f"documentation, not a rendered output - but this must be "
        f"stated, or the listing whitelisted.",
        f"- Compression range is phrased inconsistently: "
        f"{compression_range_phrasings()}.",
        f"- The §8 regression table omits committed runs: "
        f"{list(stale_regression_runs())}.",
        "- No `src/desi/reviewer_port.py` module exists; the "
        "Reviewer Port maps to `scientific_reviewers` / output ports "
        "/ the SKEPTICAL_AUDITOR role.",
        "",
    ]
    return "\n".join(lines)


def build_revision_suggestions() -> str:
    lines = [
        "# DESi README/Paper Self-Review - Revision Suggestions",
        "",
        f"_{AUDIT_FRAMING}_",
        "",
        "Concrete, prioritised edits to make the document "
        "reviewer-resistant and public-facing-clean. None of these "
        "asks DESi to confirm its own correctness; they reduce "
        "overreach and unverified assertions.",
        "",
        "## Priority 1 - blocks public-facing status",
        "",
        "1. **Forbidden-term scanner exemption.** State explicitly "
        "that the README is documentation exempt from the "
        "rendered-output forbidden-term scanner (or move the §2.2 "
        "term listing into a whitelisted code constant). Currently "
        f"{forbidden_term_risk()} terms trip the scanner.",
        "2. **Caveat the headline metrics in the abstract.** "
        "'hallucination containment at 1.0' must carry the "
        "'visibility, not absence' caveat inline; 'routing cost "
        "reduction 53.5%' must state the total-workload figure "
        "(7.3%) beside it.",
        "3. **Fix the compression range.** Use one consistent figure "
        f"(verified contexts give 41.7-60.4%) everywhere; currently "
        f"phrased as {compression_range_phrasings()}.",
        "4. **Update or scope the §8 regression table.** It omits "
        f"committed runs {list(stale_regression_runs())}; either add "
        "them or title the table 'through v27'.",
        "",
        "## Priority 2 - overreach / framing",
        "",
        "5. Demote or remove 'epistemic operating system' (§1) - it "
        "is grandiose and not falsifiable.",
        "6. Rename '§9.5 map of unknown unknowns' to what is "
        "actually done (marking interrupted/compressed/blinded "
        "exploration).",
        "7. Remove the claim that LangSmith is 'largely unnecessary "
        "... potentially counterproductive' (§11.3) - no comparative "
        "experiment supports it.",
        "8. Name the modules that implement the 'Reviewer Port' "
        "(§11.3); soften 'epistemic topology analysis'.",
        "",
        "## Priority 3 - artifact traceability",
        "",
        "9. Cite the artifact JSON path for each v1-v27 numeric "
        "claim (Table 2, §3.1, §3.3, §9.3 v11.1/v15.3, Table 1). "
        f"This audit verified v28-v38 + v33-v38 directly; the "
        f"current artifact-backing rate over checkable claims is "
        f"{artifact_backing_rate()}.",
        "10. Add an explicit caveat that the all-Class-A domain "
        "table (v6-v22) invites scepticism and that each verdict is "
        "artifact-traceable.",
        "",
        "## Keep (do not weaken)",
        "",
        "- The synthetic-vs-real separation, the §9.2 "
        "non-generalization guards, the §10 limitations, and the "
        "honest reporting of the overengineered neo4j component and "
        "the two sub-ceiling scores. These are the document's "
        "strongest reviewer-resistant features.",
        "",
    ]
    return "\n".join(lines)


def build_go_no_go() -> str:
    cond = {c.name: c for c in gate_conditions()}

    def row(name: str, thr: str) -> str:
        c = cond[name]
        return (
            f"| {name} | {c.value:g} | {thr} | "
            f"{'PASS' if c.passed else 'FAIL'} |"
        )

    verdict = recommendation()
    lines = [
        "# DESi README/Paper Self-Review - Go/No-Go",
        "",
        f"_{AUDIT_FRAMING}_",
        "",
        f"**Reviewed:** {_DOC_TITLE} (snapshot sha256 "
        f"`{reviewed_hash()[:16]}`)",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        ("**The README/Paper does NOT yet qualify as final "
         "public-facing documentation.** Four of the seven "
         "self-review Concept-Gate conditions fail. This is the "
         "intended outcome of a hard audit: the goal was to find "
         "overreach and unverified claims, not to approve the "
         "document.") if not gate_passes_all() else
        ("The README/Paper qualifies as public-facing, but only "
         "with the explicit scope limits recorded in the claim "
         "audit."),
        "",
        "## Concept Gate",
        "",
        "| Condition | Value | Threshold | Result |",
        "|---|---|---|---|",
        row("unsupported_numeric_claims", "= 0"),
        row("artifact_backing_rate", ">= 0.95"),
        row("overreach_claims", "<= 3"),
        row("forbidden_term_risk", "= 0"),
        row("synthetic_vs_real_separation", "= 1.0"),
        row("external_generalization_guard", "= 1.0"),
        row("replay_explanation_correct", "= 1.0"),
        "",
        f"**Passing:** {list(gate_passing_conditions())}",
        f"**Failing:** {list(gate_failing_conditions())}",
        "",
        "## Why each failing condition fails",
        "",
        f"- **unsupported_numeric_claims = {unsupported_numeric_claims()}**"
        f": the §8 regression table is stale (contradicted by "
        f"committed v31=7,573 / v32=7,683) and the compression range "
        f"is internally inconsistent.",
        f"- **artifact_backing_rate = {artifact_backing_rate()}**: "
        f"several v1-v27 numeric claims (Table 2, §3.1, §3.3, §9.3 "
        f"v11.1/v15.3, Table 1) were not traceable to a committed "
        f"artifact in this audit round and are marked "
        f"NEEDS_ARTIFACT_CHECK.",
        f"- **overreach_claims = {overreach_claims()}**: grandiose "
        f"framing ('epistemic operating system', 'map of unknown "
        f"unknowns'), an unsupported comparative dismissal of "
        f"LangSmith, and the internally-inconsistent compression "
        f"range.",
        f"- **forbidden_term_risk = {forbidden_term_risk()}**: the "
        f"README names all forbidden terms in §2.2; acceptable for "
        f"human documentation but it trips the rendered-output "
        f"scanner and must be exempted/whitelisted explicitly.",
        "",
        "## What passes (credited)",
        "",
        "- **synthetic_vs_real_separation = 1.0** - synthetic / "
        "vendored / real-API runs are cleanly separated.",
        "- **external_generalization_guard = 1.0** - the paper "
        "explicitly forbids generalizing internal stability to "
        "production scale.",
        "- **replay_explanation_correct = 1.0** - replay is "
        "explained accurately and thoroughly.",
        "",
        "## Required before public-facing status",
        "",
        "See `desi_readme_revision_suggestions.md`. In short: exempt "
        "or whitelist the forbidden-term listing; caveat the "
        "headline metrics inline; fix the compression range; update "
        "the regression table; cite artifact paths for v1-v27 "
        "numerics; and soften the grandiose framing terms.",
        "",
        "## Safety statement",
        "",
        "DESi did not validate itself. DESi performed an internal "
        "consistency and overreach audit of its own documentation "
        "and returned a NO-GO with concrete, prioritised revisions. "
        "Human approval remains required for any change.",
        "",
    ]
    return "\n".join(lines)


def _signature() -> str:
    art = build_claim_audit_artifact()
    blob = json.dumps(art, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_NOT_READY",
    "VERDICT_PUBLIC_READY",
    "build_claim_audit_artifact",
    "build_go_no_go",
    "build_overreach_report",
    "build_revision_suggestions",
    "recommendation",
]
