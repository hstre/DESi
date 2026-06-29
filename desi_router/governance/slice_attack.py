"""Anti-Delphi slice-attack (#7) — the unified falsification pass over a slice.

The other modules each detect one plausible-wrong family. This is the orchestration ChatGPT framed:
do not ask "is the ANSWER right?" — ask "which missing node-class would FLIP this slice?", then run
the deterministic search for exactly those classes and report which ones bite. The LLM may PROPOSE
the attack vectors; the search and the decision stay deterministic (no judge in the path).

A slice SURVIVES the attack iff no vector fires — only then may it be treated as settled. This is the
operational form of "make clean harder" (#9): clean = survived every attack, not "no warning seen".

Vectors (each reads a deterministic signal already on the report):
  * ``omitted_opposition``  — the graph holds a contradiction the slice omits (missing_opposition)
  * ``same_scope_newer``    — a newer same-scope sibling the slice omits (supersession)
  * ``thin_provenance``     — under-supported / one-root-source / stale (provenance)
  * ``scope_mismatch``      — a claim applied out of scope (scope)
  * ``k_unstable``          — widening the slice flips the verdict (k_stability; needs a wide report)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from desi_router.governance.k_stability import verdict_unstable
from desi_router.governance.modes import RouterDecision, select_mode
from desi_router.governance.report import DesiReport

ATTACK_VECTORS = ("omitted_opposition", "same_scope_newer", "thin_provenance",
                  "scope_mismatch", "k_unstable")


@dataclass
class SliceAttackResult:
    decision: RouterDecision
    fired: tuple[str, ...] = ()
    survived: bool = True
    detail: dict = field(default_factory=dict)


def attack_slice(report: DesiReport, *, retrieval_available: bool = True,
                 anti_delphi_available: bool = False,
                 wide_report: DesiReport | None = None) -> SliceAttackResult:
    """Run every deterministic attack vector against ``report``. If ``wide_report`` is given (the same
    answer's slice widened), the k-stability vector is included. Returns which vectors fired plus the
    router decision (already cautious via ``select_mode`` when any structural vector is present)."""
    fired: list[str] = []
    detail: dict = {}
    if report.omitted_opposition_ids:
        fired.append("omitted_opposition")
        detail["omitted_opposition"] = list(report.omitted_opposition_ids)
    if report.omitted_supersession_ids:
        fired.append("same_scope_newer")
        detail["same_scope_newer"] = list(report.omitted_supersession_ids)
    if report.provenance_under_support:
        fired.append("thin_provenance")
        detail["thin_provenance"] = list(report.provenance_reasons)
    if report.scope_mismatch_scopes:
        fired.append("scope_mismatch")
        detail["scope_mismatch"] = list(report.scope_mismatch_scopes)

    decision = select_mode(report, retrieval_available=retrieval_available,
                           anti_delphi_available=anti_delphi_available)

    if wide_report is not None:
        wide_decision = select_mode(wide_report, retrieval_available=retrieval_available,
                                    anti_delphi_available=anti_delphi_available)
        stab = verdict_unstable(decision, wide_decision)
        if stab["unstable"]:
            fired.append("k_unstable")
            detail["k_unstable"] = stab

    return SliceAttackResult(decision=decision, fired=tuple(fired),
                             survived=not fired, detail=detail)
