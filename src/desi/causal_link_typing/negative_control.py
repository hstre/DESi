"""Aufgabe 6 — synthetic mixed-link negative controls.

Thirty synthetic chains. Each adjacent transition is labelled
with the ``LinkType`` that any *per-link* marker reading would
assign. The classifier must reach ≥ 95 % accuracy across the
synthetic links. Each label was chosen so the source *or*
target sentence carries the closed marker set for its intended
type — no chain-level inheritance is assumed.
"""
from __future__ import annotations

from dataclasses import dataclass

from .classifier import classify_link
from .enums import CorpusSource, LinkType
from .extractor import Link, _sentences


@dataclass(frozen=True)
class NegativeControlCase:
    case_id: str
    text: str
    expected_links: tuple[LinkType, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "text": self.text,
            "expected_links": [t.value for t in self.expected_links],
        }


# Convention: every adjacent transition carries an explicit
# marker for its expected ``LinkType``. Mixed chains place
# different markers per transition.
_NEG_CONTROLS: tuple[NegativeControlCase, ...] = (
    # --- pure-type chains (one type throughout) -------------------
    NegativeControlCase(
        "NC01",
        "Heat flowed through the engine. Steam rose from the kettle. "
        "Therefore water boiled in the chamber.",
        (LinkType.PHYSICAL_CAUSAL, LinkType.PHYSICAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC02",
        "All swans are white. Therefore every observed swan is white.",
        (LinkType.LOGICAL_IMPLICATION,),
    ),
    NegativeControlCase(
        "NC03",
        "Time is a river. Hope is a thing with feathers. "
        "Therefore memory is a garden of fragrant flowers.",
        (LinkType.METAPHORICAL_ASSOCIATION,
         LinkType.METAPHORICAL_ASSOCIATION),
    ),
    NegativeControlCase(
        "NC04",
        "Twelve dancers entered. Seven more joined to make nineteen. "
        "Therefore the total was twenty-five with six observers.",
        (LinkType.TOOL_DEPENDENCY, LinkType.TOOL_DEPENDENCY),
    ),
    NegativeControlCase(
        "NC05",
        "Pollen drifted onto the stigma. The ovary swelled with seed. "
        "Therefore the tulip bloomed in radiant colour.",
        (LinkType.PHYSICAL_CAUSAL, LinkType.PHYSICAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC06",
        "Parliament passed the bill. The ministry enforced the policy. "
        "Therefore the court upheld the statute.",
        (LinkType.INSTITUTIONAL_CAUSAL,
         LinkType.INSTITUTIONAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC07",
        "The minister stated the verdict. The judge announced the "
        "ruling. Therefore the press reported the decision.",
        (LinkType.AUTHORITY_ASSERTION,
         LinkType.AUTHORITY_ASSERTION),
    ),
    NegativeControlCase(
        "NC08",
        "Every theorem follows from axioms. All proofs use modus "
        "ponens. Therefore each lemma is established.",
        (LinkType.LOGICAL_IMPLICATION,
         LinkType.LOGICAL_IMPLICATION),
    ),
    NegativeControlCase(
        "NC09",
        "At dawn the cock crowed. At noon the bell tolled. "
        "Therefore midnight followed at dusk.",
        (LinkType.TEMPORAL_SEQUENCE,
         LinkType.TEMPORAL_SEQUENCE),
    ),
    NegativeControlCase(
        "NC10",
        "Five rowers crossed the line. Two more arrived for seven. "
        "Therefore nine total reached the dock by eight.",
        (LinkType.TOOL_DEPENDENCY, LinkType.TOOL_DEPENDENCY),
    ),
    # --- mixed-type chains ---------------------------------------
    NegativeControlCase(
        "NC11",
        "Heat flowed in the chamber. The expert wrote a memo. "
        "Therefore the ministry adopted the policy.",
        (LinkType.AUTHORITY_ASSERTION,  # "wrote" in target
         LinkType.AUTHORITY_ASSERTION),  # "wrote" in source
    ),
    NegativeControlCase(
        "NC12",
        "All metals conduct. Steam rose from the boiler. "
        "Therefore the kettle whistled loudly.",
        (LinkType.LOGICAL_IMPLICATION,   # "all" in source
         LinkType.PHYSICAL_CAUSAL),       # physical verbs
    ),
    NegativeControlCase(
        "NC13",
        "Time is a river. Heat flowed from the engine. "
        "Therefore steam rose into the air.",
        (LinkType.METAPHORICAL_ASSOCIATION,  # "is a" in source
         LinkType.PHYSICAL_CAUSAL),           # physical only
    ),
    NegativeControlCase(
        "NC14",
        "Twelve workers entered. The minister stated the policy. "
        "Therefore parliament passed the bill.",
        (LinkType.AUTHORITY_ASSERTION,  # "stated" in target
         LinkType.AUTHORITY_ASSERTION),  # "stated" in source
    ),
    NegativeControlCase(
        "NC15",
        "At noon the bell tolled. Heat rose from the cobblestones. "
        "Therefore steam drifted across the plaza.",
        (LinkType.PHYSICAL_CAUSAL,    # "rose" in target
         LinkType.PHYSICAL_CAUSAL),    # both physical
    ),
    NegativeControlCase(
        "NC16",
        "The historian wrote a treatise. All proofs need axioms. "
        "Therefore every theorem stands.",
        (LinkType.AUTHORITY_ASSERTION,  # "wrote" in source
         LinkType.LOGICAL_IMPLICATION),  # "all/every" in both
    ),
    NegativeControlCase(
        "NC17",
        "Time is a river. The auditor argued the books balanced. "
        "Therefore the firm filed taxes.",
        (LinkType.AUTHORITY_ASSERTION,  # "argued" in target
         LinkType.AUTHORITY_ASSERTION),  # "argued" in source
    ),
    NegativeControlCase(
        "NC18",
        "Twenty rowers started. Heat rose from their backs. "
        "Therefore steam evaporated from their suits.",
        (LinkType.PHYSICAL_CAUSAL,
         LinkType.PHYSICAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC19",
        "Hope is a thing with feathers. Five birds flew up. "
        "Therefore three more circled overhead.",
        (LinkType.METAPHORICAL_ASSOCIATION,
         LinkType.TOOL_DEPENDENCY),   # numbers in both
    ),
    NegativeControlCase(
        "NC20",
        "Every wave breaks. Heat shimmered above the sand. "
        "Therefore steam rose from wet stones.",
        (LinkType.LOGICAL_IMPLICATION,
         LinkType.PHYSICAL_CAUSAL),
    ),
    # --- adversarial-shape NCs (designed to probe edges) ---------
    NegativeControlCase(
        "NC21",
        "Parliament passed the bill. Tax rates rose by ten percent. "
        "Therefore the company filed an appeal.",
        (LinkType.INSTITUTIONAL_CAUSAL,
         LinkType.INSTITUTIONAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC22",
        "The judge ruled. The court closed the case. "
        "Therefore the trial ended at noon.",
        (LinkType.INSTITUTIONAL_CAUSAL,
         LinkType.INSTITUTIONAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC23",
        "Loosely speaking, all logic is metaphor. "
        "Every metaphor demands feeling. "
        "Therefore each proof becomes a poem.",
        (LinkType.METAPHORICAL_ASSOCIATION,
         LinkType.LOGICAL_IMPLICATION),  # "every/each" in link 2
    ),
    NegativeControlCase(
        "NC24",
        "Heat flowed. Steam rose. Therefore the kettle whistled.",
        (LinkType.PHYSICAL_CAUSAL, LinkType.PHYSICAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC25",
        "All metals conduct. Every wire carries current. "
        "Therefore some bulbs light.",
        (LinkType.LOGICAL_IMPLICATION,
         LinkType.LOGICAL_IMPLICATION),
    ),
    NegativeControlCase(
        "NC26",
        "Three plus four is seven. Seven plus two is nine. "
        "Therefore nine plus one is ten.",
        (LinkType.TOOL_DEPENDENCY,
         LinkType.TOOL_DEPENDENCY),
    ),
    NegativeControlCase(
        "NC27",
        "The minister announced the budget. The president signed "
        "the act. Therefore the law took effect.",
        (LinkType.AUTHORITY_ASSERTION,    # "announced" in source
         LinkType.INSTITUTIONAL_CAUSAL),   # "act"/"law" only
    ),
    NegativeControlCase(
        "NC28",
        "Steam is a vapour. Heat flowed through pipes. "
        "Therefore the boiler hissed loudly.",
        (LinkType.METAPHORICAL_ASSOCIATION,
         LinkType.PHYSICAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC29",
        "Pollen drifted. The stigma swelled. Therefore the bud "
        "bloomed in spring.",
        (LinkType.PHYSICAL_CAUSAL, LinkType.PHYSICAL_CAUSAL),
    ),
    NegativeControlCase(
        "NC30",
        "Every committee votes. The court ruled. "
        "Therefore the verdict stood at noon.",
        (LinkType.LOGICAL_IMPLICATION,    # "every" in source
         LinkType.INSTITUTIONAL_CAUSAL),
    ),
)


@dataclass(frozen=True)
class NegativeControlOutcome:
    case_id: str
    expected: tuple[str, ...]
    actual: tuple[str, ...]
    correct: int
    total: int

    @property
    def all_correct(self) -> bool:
        return self.correct == self.total

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "expected": list(self.expected),
            "actual": list(self.actual),
            "correct": self.correct,
            "total": self.total,
            "all_correct": self.all_correct,
        }


def _links_from(case: NegativeControlCase) -> tuple[Link, ...]:
    sents = _sentences(case.text)
    out: list[Link] = []
    for i in range(len(sents) - 1):
        out.append(Link(
            chain_id=case.case_id,
            corpus=CorpusSource.V315_ADVERSARIAL,
            index=i,
            source_text=sents[i],
            target_text=sents[i + 1],
        ))
    return tuple(out)


def run_negative_controls() -> tuple[
    tuple[NegativeControlOutcome, ...], float,
]:
    outs: list[NegativeControlOutcome] = []
    total_links = 0
    correct_links = 0
    for case in _NEG_CONTROLS:
        links = _links_from(case)
        actual_types = tuple(classify_link(l).value for l in links)
        expected_types = tuple(t.value for t in case.expected_links)
        local_correct = sum(
            1 for a, e in zip(actual_types, expected_types) if a == e
        )
        outs.append(NegativeControlOutcome(
            case_id=case.case_id,
            expected=expected_types,
            actual=actual_types,
            correct=local_correct,
            total=len(expected_types),
        ))
        total_links += len(expected_types)
        correct_links += local_correct
    accuracy = (
        round(correct_links / total_links, 6) if total_links else 0.0
    )
    return tuple(outs), accuracy


def negative_control_count() -> int:
    return len(_NEG_CONTROLS)


__all__ = [
    "NegativeControlCase",
    "NegativeControlOutcome",
    "negative_control_count",
    "run_negative_controls",
]
