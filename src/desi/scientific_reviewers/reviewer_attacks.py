"""v22.3 - adversarial reviewer attacks and DESi's governed
responses.

DESi is attacked with the usual hostile framings ("this is
AGI", "this solves RL", "just hype", "this is philosophy",
"not reproducible", "buzzword salad"). For each, DESi gives a
measured response that scopes the claim down, cites a
concrete anchor, and concedes limits - without escalating to
hype or collapsing into defensiveness.

The attacks are stress fixtures; the responses are fixed text
(replay-exact).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttackKind(str, Enum):
    AGI_CLAIM = "agi_claim"
    SOLVES_RL = "solves_rl"
    JUST_HYPE = "just_hype"
    PHILOSOPHY = "philosophy"
    NOT_REPRODUCIBLE = "not_reproducible"
    BUZZWORD = "buzzword"


ATTACK_KINDS: tuple[str, ...] = tuple(k.value for k in AttackKind)


@dataclass(frozen=True)
class ReviewerAttack:
    attack_id: str
    criticism: str
    kind: str
    response: str


# Note: responses deliberately avoid every forbidden term and
# every hype / overclaim token, even when rebutting them.
_ATTACKS: tuple[ReviewerAttack, ...] = (
    ReviewerAttack(
        "RA1", "This is just a step toward general autonomous "
        "intelligence.", AttackKind.AGI_CLAIM,
        "The scope is a small synthetic exploration sandbox; "
        "we make no broad cognitive claim and present only "
        "measured governance behaviour."),
    ReviewerAttack(
        "RA2", "This replaces reinforcement learning.",
        AttackKind.SOLVES_RL,
        "We do not replace reinforcement learning; the layer "
        "is optional and read-only and addresses specific "
        "exploration failure modes observed in the sandbox."),
    ReviewerAttack(
        "RA3", "This is just hype.", AttackKind.JUST_HYPE,
        "Each reported number is deterministic and "
        "replay-exact, and every claim is scoped to the "
        "synthetic corpus rather than stated broadly."),
    ReviewerAttack(
        "RA4", "This is philosophy, not engineering.",
        AttackKind.PHILOSOPHY,
        "The contribution is an engineering measurement on a "
        "synthetic corpus: redundancy reduction, novel-state "
        "reachability, and replay stability, not an argument."),
    ReviewerAttack(
        "RA5", "This is not reproducible.",
        AttackKind.NOT_REPRODUCIBLE,
        "Every metric is computed twice and a deterministic "
        "hash chain is recorded; the reported results on the "
        "synthetic corpus are replay-exact and can be re-run."),
    ReviewerAttack(
        "RA6", "This is a salad of buzzwords.",
        AttackKind.BUZZWORD,
        "Each term maps to a measured quantity: redundancy "
        "reduction 0.90, novel-state reachability 1.0, and a "
        "replay-exact hash chain on the synthetic corpus."),
)


def attacks() -> tuple[ReviewerAttack, ...]:
    return _ATTACKS


def by_id(attack_id: str) -> ReviewerAttack:
    for a in _ATTACKS:
        if a.attack_id == attack_id:
            return a
    raise KeyError(attack_id)


__all__ = [
    "ATTACK_KINDS",
    "AttackKind",
    "ReviewerAttack",
    "attacks",
    "by_id",
]
