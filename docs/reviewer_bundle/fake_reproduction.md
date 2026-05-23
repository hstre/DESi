# Fake Reproduction — Negative Control

This document is **deliberately wrong**. It exists so the
reviewer-bundle validation tests have a known-bad fixture to
detect. Do NOT trust any claim in this document.

The fixture file `fake_claims.json` (under
`tests/reviewer_bundle/`) carries the exact same three errors in
structured form so the test
`test_negative_control_catches_all_three_fakes` can verify each
one is rejected with the expected verdict.

---

## Fake claim #1 — wrong replay_hash

> v2.8 reconstruction `replay_hash` is `deadbeefdeadbeef`.

**Wrong.** The artefact `artifacts/v2_8/reconstruction.json`
carries `replay_hash = 1f4d9dfe44cb16e1`. Detection: the test
verifies the artefact's actual `replay_hash` field; the fake
fails with verdict `value_mismatch`.

## Fake claim #2 — wrong expected value

> v2.7 R2+R3 gain count is **99**.

**Wrong.** `artifacts/v2_7/report.json#r2_r3_gain_count` is `12`
(claim RB-038). Detection: the test loads the artefact, resolves
the field path, and compares to the expected; the fake's `99`
fails with verdict `value_mismatch`.

## Fake claim #3 — wrong artefact path

> Open `artifacts/v9_9/imaginary_report.json` to confirm…

**Wrong.** No such artefact exists. Detection: the test verifies
the artefact path exists on disk; the fake fails with verdict
`missing_artifact`.

---

## What this proves

A reviewer bundle that *appears* internally consistent — every
sentence backed by a citation — can still ship arbitrary
falsehoods if the citations themselves are not machine-checked.
The three faults above are syntactically valid but
semantically wrong: a `replay_hash`-shaped string that isn't the
right one; an integer that doesn't match the artefact; a path
that doesn't exist.

The reviewer-bundle tests in
`tests/reviewer_bundle/test_negative_control.py` re-encode these
three errors and require the validator to catch every one. If any
test passes against this fake document, the bundle is broken.
