"""A deterministic in-memory ontology adapter — for tests, fixtures, and a small curated seed.

No corpus, no network: a fixed term -> senses table. This is what lets the probe's consumer rules be
unit-tested and replay-stable without WordNet/OpenCyc installed, and what a future small hand-curated
'known ambiguous terms' seed would use. It is NOT a knowledge base — it asserts nothing beyond what is
written into it, and like every adapter its output is ``may_gate=False``.
"""
from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Sequence as _Seq

from desi_router.ontology_probe.base import Sense


class StaticOntologyAdapter:
    source = "static"

    def __init__(self, table: Mapping[str, _Seq[Sense]], *, source: str = "static") -> None:
        self.source = source
        self._t: dict[str, tuple[Sense, ...]] = {
            (k or "").strip().lower(): tuple(v) for k, v in table.items()
        }

    def senses(self, term: str) -> tuple[Sense, ...]:
        return self._t.get((term or "").strip().lower(), ())
