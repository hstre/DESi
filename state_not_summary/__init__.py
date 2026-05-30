"""DESi State (not Summary) — Prototype 2.

Hypothesis under test: epistemic STATES are a better long-term context than compressed
narratives. The state stores no prose, no chat summary, no conversational history.

State categories (the ONLY allowed contents):
  * active_claims        : Claim-ID, status, evidence
  * active_constraints   : Rule-ID, rule body, scope
  * open_conflicts       : Conflict-ID, claim_ids involved, status
  * decisions            : Decision-ID, body, active_since, replaces?
  * discarded_paths      : Path-ID, body, single-sentence reason
  * open_questions       : Question-ID, body, blocking?
  * evidence_status      : domain -> {established|likely|unclear|untested}

What is forbidden in the state (per the brief):
  chat summaries · prose · narratives · dialog excerpts · full arguments · history

The extractor is structural: it emits IDs, statuses and short canonical bodies — never
a paragraph. Round-trip via parse() to verify nothing leaks back as prose.
"""
