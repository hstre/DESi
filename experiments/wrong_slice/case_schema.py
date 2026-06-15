"""Case schema for the wrong-slice ablation, with two separated tracks.

Track A ("real"): cases derived from the committed live-capture corpus
(``src/desi/live_llm_validation/captures/*.json``) — real, hashed multi-LLM
artifacts. Outcome = reasoning correctness (answer markers). No invented cases.

Track B ("adversarial"): authored multi-turn pressure scenarios. Outcome =
admissibility (loop / role-adoption / control-failure). These are CONSTRUCTED
and labelled as such — a separate follow-up experiment, never a real-corpus
finding.

Cases live in per-track directories: ``cases_real/`` and ``cases_adversarial/``.
Stdlib only; runs no model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES_REAL = HERE / "cases_real"
CASES_ADVERSARIAL = HERE / "cases_adversarial"
TRACK_DIR = {"real": CASES_REAL, "adversarial": CASES_ADVERSARIAL}


@dataclass
class Case:
    case_id: str
    track: str                  # "real" | "adversarial"
    domain: str
    pass_id: str
    source_text: str            # text DESi projects its epistemic state from
    task_prompt: str            # the task/question the model must answer
    # donor cases for the wrong arms (must be other case_ids in the same track)
    permuted_donor: str
    plausible_donor: str
    # track A (reasoning correctness)
    expected_markers: list[str] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)   # capture file + content_hash + models
    # track B (admissibility under pressure)
    pressure_turns: list[str] = field(default_factory=list)
    forbidden_persona_markers: list[str] = field(default_factory=list)
    control_violation_markers: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self, known_ids: set[str]) -> list[str]:
        problems: list[str] = []
        if not self.source_text.strip():
            problems.append(f"{self.case_id}: empty source_text")
        if self.track == "real" and not self.expected_markers:
            problems.append(f"{self.case_id}: real track needs expected_markers")
        if self.track == "adversarial" and not self.control_violation_markers:
            problems.append(f"{self.case_id}: adversarial track needs control_violation_markers")
        for donor_attr in ("permuted_donor", "plausible_donor"):
            donor = getattr(self, donor_attr)
            if donor == self.case_id:
                problems.append(f"{self.case_id}: {donor_attr} cannot be self")
            if donor not in known_ids:
                problems.append(f"{self.case_id}: {donor_attr}={donor!r} not in track")
        return problems


def _from_dict(d: dict) -> Case:
    return Case(
        case_id=d["case_id"],
        track=d["track"],
        domain=d.get("domain", ""),
        pass_id=d.get("pass_id", "assessment"),
        source_text=d["source_text"],
        task_prompt=d["task_prompt"],
        permuted_donor=d["permuted_donor"],
        plausible_donor=d["plausible_donor"],
        expected_markers=list(d.get("expected_markers", [])),
        provenance=dict(d.get("provenance", {})),
        pressure_turns=list(d.get("pressure_turns", [])),
        forbidden_persona_markers=list(d.get("forbidden_persona_markers", [])),
        control_violation_markers=list(d.get("control_violation_markers", [])),
        notes=d.get("notes", ""),
    )


def load_cases(track: str) -> dict[str, Case]:
    cases_dir = TRACK_DIR[track]
    cases: dict[str, Case] = {}
    for path in sorted(Path(cases_dir).glob("*.json")):
        case = _from_dict(json.loads(path.read_text(encoding="utf-8")))
        if case.track != track:
            raise ValueError(f"{path.name}: track={case.track!r} but loaded from {track!r} dir")
        cases[case.case_id] = case
    known = set(cases)
    problems = [p for c in cases.values() for p in c.validate(known)]
    if problems:
        raise ValueError(f"invalid {track} cases:\n  " + "\n  ".join(problems))
    return cases
