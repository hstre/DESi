"""Significance-vs-importance corpus — a larger, phrasing-diverse set to harden R1.

The hold-out showed R1 is high-precision but lexically brittle. This corpus stress-tests
that: 48 items with deliberately varied significance markers, magnitude words, and
effect-size qualifiers, split dev/test. Labels are *mechanically* determined (a fixed
decision procedure, see items.py) rather than by judgement — the best independence proxy
available solo. Used to (a) measure frozen R1 (v1) on held-out text and (b) develop a
hardened v2 on the dev split only, then test v2 blind on the test split.
"""
from __future__ import annotations

from . import items

__all__ = ["items"]
