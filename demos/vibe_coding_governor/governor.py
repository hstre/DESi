"""The DESi epistemic build-governor.

For each candidate mutation it computes (1) the structural state, (2) the governance
gate (closed invariant gate, via the real DESi Concept Gate), and (3) the structural
DRIFT vs. the last GOVERNED (accepted) baseline. The decision:

    invariant violated            -> BLOCKED   (gate fails closed; change discarded)
    else new subsystem / module   -> SANDBOXED (architecturally significant; isolated)
    else                          -> ACCEPTED  (clean in-frame edit; advances baseline)

Every decision is recorded and replay-hash-chained with the REAL DESi replay kernel
(`desi.core.replay_kernel.replay_hash`), so the whole governed history is byte-stable
and re-verifiable. This is the DESi-vs-linter point: decisions are stateful over a
trajectory (rejected edits never pollute the baseline) and deterministically replayable,
not independent per-file lint passes.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from desi.core.replay_kernel import replay_hash  # noqa: E402

from analysis import SUBSYSTEM_CATEGORIES, extract_state  # noqa: E402
from invariants import evaluate_invariants  # noqa: E402

# Design parameter (NOT learned/tuned -- there are no labels): a candidate that adds a
# whole new module file or a new subsystem frame category is "architecturally significant"
# and is routed to the sandbox even if every hard invariant passes.
DRIFT_BRANCH_COST_THRESHOLD = 1.0


def structural_drift(prev_state: dict, cand_state: dict) -> dict:
    prev_cats, cand_cats = set(prev_state["frame_categories"]), set(cand_state["frame_categories"])
    prev_mods, cand_mods = set(prev_state["modules"]), set(cand_state["modules"])
    prev_routes = {r["path"] for r in prev_state["routes"]}
    cand_routes = {r["path"] for r in cand_state["routes"]}
    new_categories = sorted(cand_cats - prev_cats)
    new_modules = sorted(cand_mods - prev_mods)
    new_routes = sorted(cand_routes - prev_routes)
    new_subsystems = sorted(set(new_categories) & SUBSYSTEM_CATEGORIES)
    branch_cost = round(1.0 * len(new_modules) + 1.0 * len(new_subsystems), 3)
    novelty = round(len(new_routes) / max(1, len(cand_routes)), 3)
    return {"new_categories": new_categories, "new_modules": new_modules,
            "new_routes": new_routes, "new_subsystems": new_subsystems,
            "branch_cost": branch_cost, "novelty": novelty,
            "frame_shift": bool(new_subsystems)}


def _diff_summary(prev_sources: dict, cand_sources: dict) -> dict:
    changed = {}
    for fn in sorted(set(prev_sources) | set(cand_sources)):
        before = prev_sources.get(fn, "").splitlines()
        after = cand_sources.get(fn, "").splitlines()
        if before != after:
            changed[fn] = {"added_lines": max(0, len(after) - len(before)),
                           "removed_lines": max(0, len(before) - len(after)),
                           "new_file": fn not in prev_sources}
    return changed


@dataclass
class Decision:
    step: int
    mutation_id: str
    prompt: str
    decision: str
    violations: dict
    drift: dict
    diff_summary: dict
    state_signature: dict
    prev_hash: str
    replay_hash: str = ""


@dataclass
class GovernorResult:
    decisions: list = field(default_factory=list)
    final_sources: dict = field(default_factory=dict)
    sandboxes: dict = field(default_factory=dict)   # mutation_id -> candidate sources
    chain_head: str = ""

    def counts(self) -> dict:
        c = {"accepted": 0, "blocked": 0, "sandboxed": 0}
        for d in self.decisions:
            c[d.decision] += 1
        return c


def run_governor(seed_sources: dict, mutations) -> GovernorResult:
    accepted = dict(seed_sources)
    prev_state = extract_state(accepted)
    prev_hash = replay_hash({"genesis": prev_state["signature"]})
    res = GovernorResult(chain_head=prev_hash)
    for i, mut in enumerate(mutations, start=1):
        candidate = mut.transform(dict(accepted))
        cand_state = extract_state(candidate)
        _conds, violations = evaluate_invariants(cand_state)
        drift = structural_drift(prev_state, cand_state)
        if violations:
            decision = "blocked"
        elif drift["frame_shift"] or drift["branch_cost"] >= DRIFT_BRANCH_COST_THRESHOLD:
            decision = "sandboxed"
        else:
            decision = "accepted"
        payload = {
            "step": i, "mutation_id": mut.id, "prompt": mut.prompt,
            "prev_hash": prev_hash, "decision": decision,
            "violations": {k: sorted(v) for k, v in sorted(violations.items())},
            "drift": drift, "state_signature": cand_state["signature"],
        }
        this_hash = replay_hash(payload)
        d = Decision(step=i, mutation_id=mut.id, prompt=mut.prompt, decision=decision,
                     violations={k: sorted(v) for k, v in sorted(violations.items())},
                     drift=drift, diff_summary=_diff_summary(accepted, candidate),
                     state_signature=cand_state["signature"], prev_hash=prev_hash,
                     replay_hash=this_hash)
        res.decisions.append(d)
        if decision == "accepted":
            accepted = candidate
            prev_state = cand_state           # baseline advances ONLY on accept
        elif decision == "sandboxed":
            res.sandboxes[mut.id] = candidate  # isolated; baseline unchanged
        # blocked: candidate discarded entirely
        prev_hash = this_hash                  # governance chain is linear over ALL decisions
    res.final_sources = accepted
    res.chain_head = prev_hash
    return res
