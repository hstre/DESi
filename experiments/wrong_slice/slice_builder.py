"""Steps 1 & 3: build the four arms' slices from frozen claims (OFFLINE).

Given the frozen per-case claim files produced by ``extract.py``, this builds:

  * correct        — this case's claims, the pass-appropriate slice
  * wrong_permuted — claims from a cross-context donor case, strictly matched
  * wrong_plausible— claims from a same-domain donor case, strictly matched

Wrong arms are gated by ``slice_matcher.match`` against the correct slice and any
that fail are **discarded and audited** (never patched). Matching token length
across naturally different texts is done by searching the donor's claims for the
size-N subset whose rendered token length is closest to the correct slice, then
the matcher enforces the tolerance. Deterministic and offline — no model calls.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from slice_matcher import (
    Claim,
    Slice,
    content_hash,
    default_token_count,
    match,
    render_slice,
)

FROZEN_DIR = Path(__file__).resolve().parent / "frozen"

# fixed status/provenance field schema, identical across all claims/cases so the
# schema dimensions of the matcher are satisfied by construction.
SECTION_BY_MODALITY = {
    "established": "facts",
    "evidence": "facts",
    "hypothesis": "hypotheses",
    "suggestion": "hypotheses",
}
DEFAULT_SECTION = "hypotheses"
OUTLINE = ["facts", "hypotheses"]
TOKEN_TOLERANCE = 12
MAX_SUBSET_SEARCH = 14  # cap combinatorics; donor lists are small


def _claim_from_record(rec: dict) -> Claim:
    content = " | ".join(
        x for x in (rec.get("subject", ""), rec.get("predicate", ""), rec.get("object", "")) if x
    ) or rec.get("object", "") or rec.get("subject", "")
    modality = rec.get("modality", "hypothesis")
    return Claim(
        text=content,
        status={"status": rec.get("status", "unknown"), "modality": modality},
        provenance={
            "generated_by": rec.get("generated_by", "llm_semantic_projection"),
            "evidence_refs": ",".join(rec.get("evidence_refs", [])),
        },
        section=SECTION_BY_MODALITY.get(modality, DEFAULT_SECTION),
    )


def _slice_from_records(records: list[dict], pass_id: str) -> Slice:
    claims = [_claim_from_record(r) for r in records]
    return Slice(claims=claims, pass_id=pass_id, outline=list(OUTLINE))


def load_frozen_claims(case_id: str, frozen_dir: Path = FROZEN_DIR) -> list[dict]:
    path = Path(frozen_dir) / f"{case_id}.claims.json"
    return json.loads(path.read_text(encoding="utf-8"))["claims"]


@dataclass
class ArmSlice:
    arm: str
    slice: Slice
    matcher_ok: bool | None
    slice_hash: str


def _best_matched_subset(correct: Slice, donor_records: list[dict], pass_id: str,
                         *, token_tolerance: int) -> Slice | None:
    """Search donor claims for an N-claim subset that matches `correct`."""
    n = len(correct.claims)
    if len(donor_records) < n:
        return None
    target = default_token_count(render_slice(correct))
    pool = donor_records[:MAX_SUBSET_SEARCH]
    best: tuple[int, Slice] | None = None
    for combo in combinations(range(len(pool)), n):
        cand = _slice_from_records([pool[i] for i in combo], pass_id)
        rep = match(correct, cand, token_tolerance=token_tolerance)
        if rep.ok:
            tok = default_token_count(render_slice(cand))
            score = abs(tok - target)
            if best is None or score < best[0]:
                best = (score, cand)
    return best[1] if best else None


def build_arms(case_id: str, pass_id: str, permuted_donor: str, plausible_donor: str,
               *, frozen_dir: Path = FROZEN_DIR, token_tolerance: int = TOKEN_TOLERANCE,
               audit_sink=None) -> dict[str, ArmSlice]:
    """Build correct + the two wrong arms. Returns {arm: ArmSlice}.

    Raises if a wrong arm cannot be matched (audited first if a sink is given) —
    it never returns an unmatched wrong slice.
    """
    from audit import admit_or_audit  # local import keeps slice_builder importable standalone

    correct = _slice_from_records(load_frozen_claims(case_id, frozen_dir), pass_id)
    arms: dict[str, ArmSlice] = {
        "correct": ArmSlice("correct", correct, None, content_hash(correct)),
    }
    for arm, donor in (("wrong_permuted", permuted_donor), ("wrong_plausible", plausible_donor)):
        cand = _best_matched_subset(
            correct, load_frozen_claims(donor, frozen_dir), pass_id,
            token_tolerance=token_tolerance,
        )
        if cand is None:
            if audit_sink is not None:
                # record the failure honestly (best-effort full-donor report)
                donor_slice = _slice_from_records(load_frozen_claims(donor, frozen_dir), pass_id)
                admit_or_audit(correct, donor_slice, audit_sink,
                               context={"case": case_id, "arm": arm, "donor": donor},
                               token_tolerance=token_tolerance)
            raise ValueError(
                f"{case_id}/{arm}: no token-matched subset from donor {donor!r} "
                f"within tolerance {token_tolerance}; candidate discarded (audited)."
            )
        ok = True
        if audit_sink is not None:
            ok, _ = admit_or_audit(correct, cand, audit_sink,
                                   context={"case": case_id, "arm": arm, "donor": donor},
                                   token_tolerance=token_tolerance)
        arms[arm] = ArmSlice(arm, cand, ok, content_hash(cand))
    return arms
