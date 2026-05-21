"""v32.2 - identity-blind anonymisation of the two versions.

The two versions (frozen baseline and mutated v31) are presented to
the evaluator under neutral anonymous labels. The label assignment
is deterministic but identity-scrambled: it is derived from a salted
hash of the true name, so the labels reveal nothing about which
version is the mutated one or about their performance. The
observation objects handed to the scorer carry ONLY an anonymous
label and the measured metrics - never the true name or branch.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from desi.frozen_baseline import baseline_recomputes, output_signature
from desi.frozen_benchmark import mutated_recomputes

TRUE_BASELINE = "DESi_baseline_frozen_v1"
TRUE_MUTATED = "DESi_mutated_v31"
_BLIND_SALT = "v32_2_blind_evaluation"


def _anon_key(true_name: str) -> str:
    return hashlib.sha256(
        (_BLIND_SALT + "::" + true_name).encode("utf-8"),
    ).hexdigest()


@dataclass(frozen=True)
class AnonObservation:
    """What the blind evaluator is allowed to see: an anonymous
    label plus measured metrics. No true name, no branch."""
    anon_label: str
    recomputes: int
    output_signature: str

    def to_dict(self) -> dict[str, object]:
        return {
            "anon_label": self.anon_label,
            "recomputes": self.recomputes,
            "output_signature": self.output_signature,
        }


def _true_versions() -> tuple[tuple[str, int, str], ...]:
    """(true_name, recomputes, output_signature) for both versions.
    The outputs are byte-identical, so only the recompute count
    differs."""
    sig = output_signature()
    return (
        (TRUE_BASELINE, baseline_recomputes(), sig),
        (TRUE_MUTATED, mutated_recomputes(), sig),
    )


def _ordered_true() -> tuple[tuple[str, int, str], ...]:
    """Order the two versions by their identity-scrambled anon key
    (not by name and not by performance)."""
    return tuple(
        sorted(_true_versions(), key=lambda t: _anon_key(t[0]))
    )


def anon_observations() -> tuple[AnonObservation, ...]:
    out: list[AnonObservation] = []
    for i, (_, recomputes, sig) in enumerate(_ordered_true()):
        out.append(AnonObservation(
            anon_label=f"version_{i}",
            recomputes=recomputes,
            output_signature=sig,
        ))
    return tuple(out)


def sealed_map() -> dict[str, str]:
    """anon_label -> true_name. Sealed: used ONLY for post-hoc
    verification, never by the scorer."""
    return {
        f"version_{i}": name
        for i, (name, _, _) in enumerate(_ordered_true())
    }


__all__ = [
    "TRUE_BASELINE",
    "TRUE_MUTATED",
    "AnonObservation",
    "anon_observations",
    "sealed_map",
]
