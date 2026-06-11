"""Documents a known limitation of the confidence heuristic: its hedging /
refusal markers are English-only.

This is not a bug to fix here — it is behaviour the calibration story depends
on. The discrimination numbers are derived from an English-language benchmark,
so a German (or any non-English) deployment would get systematically miscalibrated
confidence: a hedged German answer reads as 'high', defeating the escalation gate.
Pinning it makes the limitation visible to whoever extends the heuristic.
"""
from __future__ import annotations

from desi_router.answerer import _heuristic_confidence


def test_english_hedging_is_detected_as_low():
    assert _heuristic_confidence("I don't have enough information to answer this.") == "low"
    assert _heuristic_confidence("I cannot determine the answer from the context.") == "low"


def test_german_hedging_is_missed_and_reads_as_high():
    # A clearly hedged German answer ("I can't determine that from the
    # documents") carries none of the English markers, so the heuristic
    # mislabels it as confident. Documenting the blind spot, not endorsing it.
    hedged_de = "Das lässt sich aus den vorliegenden Unterlagen leider nicht bestimmen."
    assert _heuristic_confidence(hedged_de) == "high"


def test_blindspot_is_in_the_markers_not_the_length_guard():
    # The short-answer guard still fires regardless of language, so use a long
    # German hedge to isolate that it is the *markers* that are English-only.
    long_hedged_de = (
        "Ich bin mir nicht sicher und kann das anhand der bereitgestellten "
        "Informationen nicht eindeutig beantworten oder verifizieren."
    )
    assert len(long_hedged_de.strip()) >= 10          # length guard does not apply
    assert _heuristic_confidence(long_hedged_de) == "high"  # markers miss it
