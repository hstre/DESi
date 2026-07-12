"""HARD2 HOLD-OUT — a separate, blind test set for the frozen deterministic rules.

The rules in ``..hard2.rules`` were developed using the 18 hard2 items as a
*development signal* and frozen by commit. This hold-out is authored independently
(new items + paraphrases of hard2, including adversarial phrasings designed to
*stress* the frozen rules — some deliberately evade R1's lexicon). It exists to test
the rules blind: whatever they do here is reported honestly, with no rule edits.
"""
from __future__ import annotations

from . import items, prompt

__all__ = ["items", "prompt"]
