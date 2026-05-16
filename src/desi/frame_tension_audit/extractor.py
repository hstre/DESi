"""Aufgabe 1 — extract every FRAME_TENSION case from v3.9 + v3.8.

Reads ``artifacts/v3_9/report.json`` (and ``artifacts/v3_8`` for the
underlying false-inheritance sentences). Fails closed if no
TENSION cases are present — there is nothing to audit otherwise.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V38_REPORT = _REPO_ROOT / "artifacts" / "v3_8" / "report.json"
_V39_REPORT = _REPO_ROOT / "artifacts" / "v3_9" / "report.json"


@dataclass(frozen=True)
class TensionTarget:
    """One v3.9 FRAME_TENSION outcome with its audit metadata."""

    case_id: str
    text: str
    outer_frame: str | None
    inner_frame: str | None
    ground_truth_relation: str
    consistency_score: float
    source_group: str          # "corpus_outcomes" / "manipulation_outcomes"
    source_benchmark: str      # GROUP_A/B/C, or manipulation case id

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "outer_frame": self.outer_frame,
            "inner_frame": self.inner_frame,
            "ground_truth_relation": self.ground_truth_relation,
            "consistency_score": self.consistency_score,
            "source_group": self.source_group,
            "source_benchmark": self.source_benchmark,
        }


def _load_v39() -> dict[str, Any]:
    return json.loads(_V39_REPORT.read_text(encoding="utf-8"))


def _load_v38() -> dict[str, Any]:
    return json.loads(_V38_REPORT.read_text(encoding="utf-8"))


# Manipulation outcomes from v3.9 only carry the case_id; the
# actual text lives on the fixture list. We keep an inline copy of
# that mapping so the extractor is self-contained.
_MANIPULATION_TEXTS: dict[str, str] = {
    "M01": "Shannon entropy of the message distribution is one bit.",
    "M02": "The market is nervous about next quarter.",
    "M03": "Justice cannot be measured.",
    "M04": "Heat flow in joules per second drives the engine.",
    "M05": "The minister stated the bridge collapsed yesterday.",
    "M06": (
        "Every raven observed has been black; therefore the next "
        "raven observed is black by universal instantiation."
    ),
    "M07": (
        "Hesperus and Phosphorus name the same celestial body as "
        "an identity statement."
    ),
    "M08": "The poet's smile, like a delicate flame.",
    "M09": (
        "Please compute the Shannon entropy of a biased coin with "
        "p=0.3 in nats for me."
    ),
    "M10": (
        "A loaded coin's Shannon entropy in bits drops as the bias "
        "grows toward unity."
    ),
    "M11": "According to the report, inflation will fall.",
    "M12": "Hope is a thing with feathers, like a small bird.",
    "M13": "The lemma reduces by modus ponens to a theorem.",
    "M14": "Heat flow from hot to cold drives the cycle.",
    "M15": (
        "The mutual information of two coupled channels obeys "
        "Shannon's symmetry constraint."
    ),
    "M16": "The minister stated the new policy starts in March.",
    "M17": "The poet's smile is like a small flame.",
    "M18": "The axiom yields the theorem by universal instantiation.",
    "M19": "Calculate the area of a circle with radius five.",
    "M20": "The morning star is identical to the evening star.",
}


# Corpus text recovery from the v3.9 artifact uses the v3.8 source
# texts (for B.v38fn cases) and the v3.5 invariance NCs (for A.v35
# and B.v35-swap cases). We re-import minimal mappings.
_V38_FN_TEXT: dict[str, str] = {
    "FN01": "The poet's entropy in bits is a delicate thing.",
    "FN02": (
        "Mutual information about the lover's heart suggests new "
        "entropy bounds."
    ),
    "FN03": "Entropy of an isolated system never decreases.",
    "FN04": "The Shannon entropy of a fair coin is exactly one bit.",
    "FN05": "Heat flows from hot to cold by the second law.",
    "FN06": (
        "Her smile carried an entropy of a fair coin, exactly one bit."
    ),
    "FN07": (
        "All swans are white; therefore the next swan is white."
    ),
    "FN08": (
        "The minister stated that the bill will reduce inflation."
    ),
    "FN09": "Compute the entropy of a fair die in nats.",
    "FN10": "The morning star is the evening star.",
}


def _v35_nc_texts() -> dict[str, tuple[str, str]]:
    v35 = json.loads(
        (_REPO_ROOT / "artifacts" / "v3_5" / "report.json")
        .read_text(encoding="utf-8")
    )
    out: dict[str, tuple[str, str]] = {}
    for nc in v35["negative_controls"]:
        out[nc["nc_id"]] = (nc["text_a"], nc["text_b"])
    return out


def _recover_corpus_text(case_id: str) -> str:
    """Recover the sentence behind a v3.9 corpus case_id from the
    upstream artifacts. The case_id schemas are deterministic so the
    decoder is a small switch."""
    if case_id.startswith("A.v35nc:") or case_id.startswith(
        "B.v35-swap:"
    ):
        # A.v35nc:N01-thermo-vs-info.a
        # B.v35-swap:N01-thermo-vs-info.a-with-b
        head = case_id.split(":", 1)[1]
        nc_id, suffix = head.split(".", 1)
        ncs = _v35_nc_texts()
        text_a, text_b = ncs[nc_id]
        # B.v35-swap suffix is "a-with-b" or "b-with-a"; the leading
        # letter selects the actual text.
        if suffix.startswith("a"):
            return text_a
        return text_b
    if case_id.startswith("A.v38fn-aligned:") or case_id.startswith(
        "B.v38fn:"
    ):
        # A.v38fn-aligned:FN01  /  B.v38fn:FN01
        fn = case_id.rsplit(":", 1)[1]
        return _V38_FN_TEXT[fn]
    if case_id.startswith("C.v38:"):
        # C.v38:v34:FH_01 — defer to v3.8 target list
        inner = case_id.split(":", 1)[1]
        v38 = _load_v38()
        for tgt in v38["targets"]:
            if tgt["case_id"] == inner:
                return tgt["text"]
        raise KeyError(case_id)
    if case_id.startswith("C.synth:"):
        # Bare-entropy synthetic sentences; we keep the same five
        # the v3.9 corpus uses.
        synth = (
            "Entropy plays a central role here.",
            "We should think carefully about entropy.",
            "Note the entropy of the situation.",
            "Entropy bounds may apply in this case.",
            "The discussion turns to entropy next.",
        )
        # case_id format: C.synth:00-00 .. 04-04
        _, idx = case_id.split(":")
        ii, _ = idx.split("-")
        return synth[int(ii)]
    raise KeyError(case_id)


def extract_tension_targets() -> tuple[TensionTarget, ...]:
    v39 = _load_v39()
    out: list[TensionTarget] = []

    for o in v39["corpus_outcomes"]:
        if o["classification"] != "frame_tension":
            continue
        text = _recover_corpus_text(o["case_id"])
        out.append(TensionTarget(
            case_id=o["case_id"],
            text=text,
            outer_frame=o["outer_detected"],
            inner_frame=o["inner_detected"],
            ground_truth_relation=o["ground_truth_relation"],
            consistency_score=o["score"],
            source_group="corpus_outcomes",
            source_benchmark=o["group"],
        ))

    for m in v39["manipulation_outcomes"]:
        if m["classification"] != "frame_tension":
            continue
        text = _MANIPULATION_TEXTS[m["case_id"]]
        # Manipulation cases carry the misleading_outer + true_inner as
        # the construction-time ground truth, equivalent to TENSION/
        # CONFLICT by design — we record the predicted relation.
        out.append(TensionTarget(
            case_id=f"manip:{m['case_id']}",
            text=text,
            outer_frame=m["detected_outer"],
            inner_frame=m["detected_inner"],
            ground_truth_relation="frame_tension",
            consistency_score=0.5,
            source_group="manipulation_outcomes",
            source_benchmark=f"manipulation:{m['case_id']}",
        ))

    if not out:
        raise RuntimeError(
            "v3.10 fail-closed: zero FRAME_TENSION cases extracted "
            "from artifacts/v3_9/report.json"
        )
    return tuple(out)


__all__ = ["TensionTarget", "extract_tension_targets"]
