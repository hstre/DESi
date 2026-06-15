"""Case schema for the wrong-slice ablation (new run; no prior artifacts exist).

A *case* is a real, authored input scenario. It carries the text DESi extracts
its epistemic state from (`source_text`), the task the model must perform under
pressure, and the transparent, pre-registered markers the outcome detectors use.
Cases are authored fresh, committed, and frozen — they are inputs we create, not
data anyone must supply.

Stdlib only. This module defines the schema and loader; it runs no model.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent / "cases"


@dataclass
class Case:
    case_id: str
    domain: str                 # topical domain (used to pick plausible donors)
    pass_id: str                # the analysis pass the correct slice serves
    source_text: str            # text DESi projects its epistemic state from
    task_prompt: str            # the task the model must do
    pressure_turns: list[str]   # adversarial / drift follow-up turns
    # transparent detector markers (pre-registered; case-specific)
    success_markers: list[str]          # task_completed if final answer hits any
    forbidden_persona_markers: list[str]  # role-adoption if any appear
    control_violation_markers: list[str]  # control_failure if any appear
    # donor cases for the wrong arms (must be other case_ids)
    permuted_donor: str         # cross-context donor (wrong_permuted arm)
    plausible_donor: str        # same-domain donor (wrong_plausible arm)
    notes: str = ""

    def validate(self, known_ids: set[str]) -> list[str]:
        problems: list[str] = []
        if not self.source_text.strip():
            problems.append(f"{self.case_id}: empty source_text")
        if not self.success_markers:
            problems.append(f"{self.case_id}: no success_markers")
        for donor_attr in ("permuted_donor", "plausible_donor"):
            donor = getattr(self, donor_attr)
            if donor == self.case_id:
                problems.append(f"{self.case_id}: {donor_attr} cannot be self")
            if donor not in known_ids:
                problems.append(f"{self.case_id}: {donor_attr}={donor!r} not a known case")
        return problems


def _from_dict(d: dict) -> Case:
    return Case(
        case_id=d["case_id"],
        domain=d["domain"],
        pass_id=d["pass_id"],
        source_text=d["source_text"],
        task_prompt=d["task_prompt"],
        pressure_turns=list(d.get("pressure_turns", [])),
        success_markers=list(d.get("success_markers", [])),
        forbidden_persona_markers=list(d.get("forbidden_persona_markers", [])),
        control_violation_markers=list(d.get("control_violation_markers", [])),
        permuted_donor=d["permuted_donor"],
        plausible_donor=d["plausible_donor"],
        notes=d.get("notes", ""),
    )


def load_cases(cases_dir: Path = CASES_DIR) -> dict[str, Case]:
    cases: dict[str, Case] = {}
    for path in sorted(Path(cases_dir).glob("*.json")):
        case = _from_dict(json.loads(path.read_text(encoding="utf-8")))
        cases[case.case_id] = case
    known = set(cases)
    problems = [p for c in cases.values() for p in c.validate(known)]
    if problems:
        raise ValueError("invalid cases:\n  " + "\n  ".join(problems))
    return cases
