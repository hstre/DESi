"""v3.112 — T10 proxy verdict report.

Pflichtmetriken (directive § v3.112):

* ``epistemic_dims``
* ``proxy_dims``
* ``ambiguous_dims``
* ``validated_vocab_size``
* ``replay_stability``

Killerfrage: "Habe ich ein epistemisches Alphabet
- oder nur clevere Dataset-Shortcuts?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .verdict import (
    SMALL_VOCAB_DIMS,
    all_classifications,
    ambiguous_dims,
    epistemic_dims,
    proxy_dims,
    validated_vocab_size,
)


VALIDATED_VOCAB_MIN: int = 2


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3112Report:
    small_vocab_dims: tuple[str, ...]
    epistemic_dims: tuple[str, ...]
    proxy_dims: tuple[str, ...]
    ambiguous_dims: tuple[str, ...]
    validated_vocab_size: int
    classifications: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "small_vocab_dims":
                list(self.small_vocab_dims),
            "epistemic_dims":
                list(self.epistemic_dims),
            "proxy_dims":
                list(self.proxy_dims),
            "ambiguous_dims":
                list(self.ambiguous_dims),
            "validated_vocab_size":
                self.validated_vocab_size,
            "classifications":
                list(self.classifications),
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        epistemic_dims(),
        proxy_dims(),
        ambiguous_dims(),
        validated_vocab_size(),
    )
    b = (
        epistemic_dims(),
        proxy_dims(),
        ambiguous_dims(),
        validated_vocab_size(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3112Report:
    ed = epistemic_dims()
    pd = proxy_dims()
    ad = ambiguous_dims()
    vvs = validated_vocab_size()
    cls = all_classifications()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif vvs >= VALIDATED_VOCAB_MIN:
        verdict = "EPISTEMIC_VOCAB_VALIDATED"
    elif vvs == 1:
        verdict = "SINGLE_EPISTEMIC_DIM_ONLY"
    else:
        verdict = "NO_EPISTEMIC_VOCAB"

    rationale = (
        f"INFO: small_vocab_dims "
        f"{list(SMALL_VOCAB_DIMS)}",
        f"INFO: epistemic_dims {list(ed)}",
        f"INFO: proxy_dims {list(pd)}",
        f"INFO: ambiguous_dims {list(ad)}",
        f"{'PASS' if vvs >= VALIDATED_VOCAB_MIN else 'FAIL'}: "
        f"validated_vocab_size {vvs} "
        f"(minimum {VALIDATED_VOCAB_MIN})",
        f"INFO: classifications "
        f"{[c.to_dict() for c in cls]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3112Report(
        small_vocab_dims=SMALL_VOCAB_DIMS,
        epistemic_dims=ed,
        proxy_dims=pd,
        ambiguous_dims=ad,
        validated_vocab_size=vvs,
        classifications=tuple(
            c.to_dict() for c in cls
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_proxy_verdict_artifact(
) -> dict[str, object]:
    cls = all_classifications()
    return {
        "schema_version":
            "v3_112_t10_proxy_verdict",
        "small_vocab_dims":
            list(SMALL_VOCAB_DIMS),
        "epistemic_dims":
            list(epistemic_dims()),
        "proxy_dims": list(proxy_dims()),
        "ambiguous_dims":
            list(ambiguous_dims()),
        "validated_vocab_size":
            validated_vocab_size(),
        "classifications": [
            c.to_dict() for c in cls
        ],
    }


__all__ = [
    "VALIDATED_VOCAB_MIN",
    "V3112Report",
    "build_report",
    "build_t10_proxy_verdict_artifact",
]
