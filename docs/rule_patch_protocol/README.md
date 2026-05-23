# DESi Rule Patch Protocol

A read-only, deterministic, six-phase protocol that decides whether
a proposed change to DESi's inference rule set is **science** or
**tinkering**. Implemented in
`src/desi/rule_patch_protocol/` and first applied retroactively to
the v2.7 CAUSAL_CHAIN patch.

This document is the methodology overview. Every quantitative claim
below is replayable from the corresponding artefact under
`artifacts/` and machine-checked by `tests/protocol_docs/`.

---

## 1. Motivation

DESi's evolution from v0.1 through v2.7 produced one repeated
failure mode: a benchmark gap is observed, a "fix" is sketched, the
fix accidentally re-opens an older false-positive, the fix is
reverted, and the gap remains. v1.6 had to explicitly kill a
generic-fallback bridge mechanism that had silently regressed Cat E
philosophy and Cat C authority cases. v2.7's `CAUSAL_CHAIN` rule
could have done exactly the same thing — it did not, because v2.6
*pre-derived* the two guards that prevent it.

The protocol is the institutional memory of that experience. It
forbids any rule patch from advancing without first proving, from
observable data, that the patch will not re-open known false
positives.

## 2. Why ad-hoc patching fails

Three observed failure modes from v1.0–v2.7:

* **Confirmation bias on a positive run.** "It worked once on my
  text, so it must be correct." v2.0 showed that even a 30-step
  sandbox can produce 30/30 acceptances on a knob that is
  structurally decoupled — every "success" is a noise reading.
* **Case-specific allowlists masquerading as rules.** Any patch
  that branches on `case_id`, a literal string, or a hand-rolled
  regex over benchmark text is by construction unfalsifiable on
  new inputs.
* **Locally-valid fixes that globally regress.** v1.6 documented
  this in 8 cases (A5, A6, A7, A10, D3, E4, E5, E10) that an
  earlier generic-fallback bridge had silently accepted. Without a
  re-opening check, the same hole gets dug repeatedly.

The protocol's six phases each *falsify* one of these failure modes.

## 3. The six-phase protocol

See `phase_diagram.md` for the per-phase IO contract. In order:

1. **DISCOVERY** — the patch's predecessor read-only audits (v2.4
   bridge-entry, v2.5 rule coverage, v2.6 causal-chain probe) must
   exist as artefacts.
2. **RISK_PROBE** — the v2.6 probe's gate (known-FP reopen rate,
   authority/philosophy/metaphor touch rates, `safe_to_implement`)
   must all be clean.
3. **GUARD_SYNTHESIS** — at least two guards, every guard's
   `observable` in a closed allowlist
   (`rule_iteration_order`, `premise_kind`,
   `premise_text_substring`, `conclusion_text_substring`,
   `premise_token_graph`, `conclusion_token_overlap`,
   `premise_count`, `conclusion_kind`), no `case_id` or
   `allowlist` tokens permitted.
4. **IMPLEMENTATION** — declared touched files exist and live
   under allowed roots (`src/desi/logic/`, `tests/`, `docs/`,
   `artifacts/`).
5. **REGRESSION** — six benchmark hashes (v1.5 main, v1.9 tool,
   v2.3 multistep, v2.4 bridge audit, v2.5 rule audit, v2.6
   causal probe) identical to baseline.
6. **REPLAY_VERIFICATION** — two consecutive runs of the protocol
   produce bit-identical hashes.

Only after every phase passes does the orchestrator emit
`PatchPhase.COMPLETE`.

## 4. Replayability

Every `RulePatchRecord` carries a `replay_hash` over the canonical
JSON of its payload, with `timestamp` and `replay_hash` itself
excluded from the hash. Two protocol runs over the same
`PatchCandidate` produce byte-identical records.

`compute_benchmark_hashes()` enforces this property over the
six benchmark surfaces; `tests/protocol_docs/test_regression.py`
runs the calculation twice and asserts identity.

## 5. Regression discipline

The `REGRESSION` phase compares current benchmark hashes against
a baseline. In v2.8 the baseline and current values were captured
in the same protocol invocation (the protocol is read-only, so
they must match). Any drift between successive calls is a hard
fail with `passed = False` and the failing key in `fail_reason`.

The eight historical false-positive case ids (A5, A6, A7, A10,
D3, E4, E5, E10) are pinned in `causal_probe/risk.py` as
`KNOWN_FALSE_POSITIVE_CASE_IDS`. v2.7 passed the protocol with
`known_false_positive_reopen_rate = 0.000`.  [claim-anchor: artifact=artifacts/v2_6/report.json, field=metrics.known_false_positive_reopen_rate, expected=0.000]

## 6. Worked example: v2.7

See `worked_example_v27.md` for the full trace. Headline numbers:

| Metric | Value |
| --- | --- |
| `phase` | `complete` |
| `passed` | `true` |
| `created_guards` | 7 |
| `touched_files` | 8 |
| `benchmark_hash_before` | `aa01151d6e165bf0` |
| `benchmark_hash_after` | `aa01151d6e165bf0` |
| `replay_hash` | `1f4d9dfe44cb16e1` |
| Phase outcomes | 6/6 passed |

The full record is at `artifacts/v2_8/reconstruction.json`.

## 7. Negative control: fake patch

See `negative_control.md`. Headline numbers:

| Metric | Value |
| --- | --- |
| `phase` | `guard_synthesis` |
| `passed` | `false` |
| `created_guards` | 0 |
| `fail_reason` | `"missing_guards: at least two guards required"` |
| `replay_hash` | `d83d81ab8417c022` |

Without the protocol, this fake patch could have shipped: its
`touched_files` declaration (`src/desi/logic/inference.py`) is
plausible. The protocol's `GUARD_SYNTHESIS` phase rejects it
**before** any benchmark is touched.

## 8. Limitations

* The protocol verifies **process discipline**, not **semantic
  correctness**. A guard that claims to inspect
  `premise_text_substring` for some marker must actually do so —
  this is checked at the rule-implementation level (v2.7 tests),
  not in the protocol record.
* The six benchmark hashes are coarse. They detect drift but do
  not localise which case shifted. The
  `MultiStepBenchmarkRunner.replay_hash` per case provides the
  finer-grained signal.
* `compute_benchmark_hashes()` does not run the v2.0 sandbox or
  the v2.2 depth evolution. Both are slow, side-effect-free, and
  already replay-tested in their own suites. Adding them to the
  protocol's regression check would multiply the per-run cost by
  ~30 seconds for no marginal failure-detection gain.
* The protocol cannot prove that a *new* benchmark would not
  regress under a patch. v2.6's causal-chain probe is the model
  for how to extend coverage; future patches are expected to run
  the equivalent read-only probe over any new benchmark surface
  before adding a rule.
