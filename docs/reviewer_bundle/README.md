# DESi Reviewer Bundle

This bundle is for an external reviewer with **zero prior DESi
knowledge** and **zero access to the chat history**. It contains
everything needed to reproduce the core claims of v2.7, v2.8, v2.9,
v3.0 and v3.1 from this repository alone.

If you are a reviewer: read this file, then `quickstart.md`. The
three reproduction documents and the claim index are referenced
from there. Nothing else in this repository is required reading.

---

## What is DESi?

DESi (Dynamic Epistemic Self-inspection) is a research prototype
for **auditable inference**. It accepts plain-English propositions
("All men are mortal. Socrates is a man. Therefore Socrates is
mortal.") and decides whether the conclusion follows from the
premises under a closed set of inference rules.

DESi is not a chatbot, an LLM, or a general reasoning agent. It is
a small (<10 KLOC) Python library whose behaviour on a frozen
50-case benchmark (v1.5) and a 30-case multi-step benchmark (v2.3)
is bit-for-bit deterministic across two runs.

## What problem does it solve?

The narrow technical problem: distinguish **valid** inferences
from **fallacious** ones (denying-the-antecedent, hasty
generalisation, authority-as-evidence) under conditions where the
verdict and the reasoning trace are reviewable. DESi never invents
a bridging premise without naming it.

The methodological problem the v2.x line addresses: **how to
extend a reasoning system without re-introducing the failures the
previous version killed**. v1.6 had to retire a `generic_fallback`
bridge mechanism that silently accepted 8 main-benchmark cases
(A5, A6, A7, A10, D3, E4, E5, E10). v2.7's `CAUSAL_CHAIN` rule
could have re-introduced exactly the same failure mode. It did
not — because v2.6 *pre-derived* the two guards that prevent it.

The v2.8 protocol is the extracted, replayable form of that
discipline.

## What was actually changed in v2.7?

Exactly one file under `src/desi/logic/`:

- `inference.py`: added `InferenceRule.CAUSAL_CHAIN` (6th member
  of the closed enum) plus one new validator `_try_causal_chain`
  registered **last** in the `_VALIDATORS` dict.

One auxiliary file under `src/desi/rule_audit/`:

- `categories.py`: extended `AttemptedRule` enum to keep its 1:1
  mirror with `InferenceRule`.

Three test files added under `tests/logic/` and
`tests/rule_audit/`, two existing tests updated for the enum size
change (5 → 6), one docs file added, one artefact added.

**8 declared touched files in total.** Verified by
`artifacts/v2_8/reconstruction.json#len:touched_files` (claim
RB-045).

## What was not changed?

These directories are **byte-identical** to their state before
v2.7:

- `src/desi/consilium/`
- `src/desi/recursive/`
- `src/desi/tools/`
- `src/desi/memory/`
- `src/desi/evolution/`
- `src/desi/sandbox/`
- `src/desi/spl_adapter/`
- `src/desi/benchmark/`
- `src/desi/benchmark_multistep/`

The six benchmark surfaces produce the same `replay_hash` values
before and after v2.7. The aggregate `benchmark_hash_before ==
benchmark_hash_after == aa01151d6e165bf0` is recorded in the v2.8
reconstruction artefact (claim RB-046).

## Why should anyone trust the process?

Two structural answers, neither asking for trust:

1. **All quantitative claims in this repository's documentation
   carry inline anchors** of the form

   ```
   [claim_anchor: artifact=<path>, field=<json-path>, expected=<value>]
   ```

   (Real anchors use `claim-anchor` with a hyphen; this schema
   example uses an underscore so the v3.1 doc-anchor parser does
   not treat the README itself as a claim source.)

   Anchors are validated by `tests/doc_anchors/` and
   `tests/reviewer_bundle/test_claim_index.py`. The v3.1
   measurement: 36/36 anchors verified, 0 hash mismatches, 0
   drift findings across 35 documents. The v3.1 self-deception
   rate (claims that cannot be machine-verified against an
   artefact) dropped from 0.314 (v3.0) to **0.05144** (v3.1).

2. **The v2.7 patch was preceded by a read-only risk probe**
   (`artifacts/v2_6/report.json`) which empirically measured
   that an unguarded version of the rule would re-open zero of
   the 8 known v1.6 false-positive cases (claim RB-029) and
   touch zero authority/philosophy/metaphor cases
   (RB-030/031/032), but *would* incorrectly match 5 R4
   contradictions and 5 R5 cycles without explicit guards. The
   two derived guards (token-level + iteration-order) prevent
   exactly that.

## What this bundle contains

- `README.md` — this file.
- `quickstart.md` — ≤ 15 minutes, ≤ 15 commands, reproduce
  v2.7 + v2.8 + v3.1 against this repository.
- `reproduce_v27.md` — the v2.7 guarded `CAUSAL_CHAIN` rule.
- `reproduce_v28.md` — the v2.8 patch-protocol reconstruction.
- `reproduce_v31.md` — the v3.1 documentation claim-anchor
  discipline.
- `claim_index.md` — 60 machine-checkable claims with
  artefact paths.
- `claim_index.json` — the same index, machine-readable.
- `fake_reproduction.md` — **deliberately wrong** negative
  control with one fake hash, one fake value, one fake path.
  Validation tests verify the bundle catches all three.

## Falsifiable claims about this bundle

| Claim | Anchor |
| --- | --- |
| `total_claims >= 50` | `artifacts/v3_2/reviewer_metrics.json#total_claims` |
| `verified_claims == total_claims` | `artifacts/v3_2/reviewer_metrics.json#verified_claims` |
| `commands_required <= 15` | `artifacts/v3_2/reviewer_metrics.json#commands_required` |
| `estimated_minutes <= 15` | `artifacts/v3_2/reviewer_metrics.json#estimated_minutes` |
| `broken_links == 0` | `artifacts/v3_2/reviewer_metrics.json#broken_links` |
| `missing_paths == 0` | `artifacts/v3_2/reviewer_metrics.json#missing_paths` |
| `hash_mismatches == 0` | `artifacts/v3_2/reviewer_metrics.json#hash_mismatches` |

Every claim in this bundle is one `pytest tests/reviewer_bundle/`
away from being verified or falsified.
