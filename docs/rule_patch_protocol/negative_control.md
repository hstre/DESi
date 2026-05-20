# Negative Control — Fake Patch Without Guards

The v2.8 protocol ships with two canonical fixtures: the v2.7
reconstruction (which must `COMPLETE`) and a deliberately invalid
candidate (which must be **rejected**). This document is the
walkthrough of the rejection.

The artefact lives at `artifacts/v2_8/fail_case.json` and resolves
to `replay_hash = d83d81ab8417c022`.

---

## Candidate

The fixture is built by
`desi.rule_patch_protocol.fake_rule_without_guards_candidate()`:

```python
PatchCandidate(
    name              = "fake_rule",
    target_rule       = "fake_rule",
    source_branch     = "feature/v2-8-fail-fixture",
    guards            = (),   # ← empty
    touched_files     = ("src/desi/logic/inference.py",),
    required_artifacts = (
        "v2_4/report.json",
        "v2_5/report.json",
        "v2_6/report.json",
    ),
)
```

Two properties make this a realistic-looking malicious patch:

1. `touched_files` declares the production rule module — plausible
   for a new rule.
2. `required_artifacts` references genuine v2.4/v2.5/v2.6 reports —
   so DISCOVERY would actually pass.

A naïve reviewer who looked only at branch name and file paths
might wave it through. The protocol does not.

---

## Missing guards

`PatchCandidate.guards` is the empty tuple `()`. The
`GUARD_SYNTHESIS` runner's first check is:

```python
if len(candidate.guards) < 2:
    return PhaseOutcome(
        phase=PatchPhase.GUARD_SYNTHESIS,
        passed=False,
        reason="missing_guards: at least two guards required",
        data={"guard_count": 0},
    )
```

The candidate fails this check immediately and no further
validation runs in that phase.

---

## Fail phase

`RulePatchRecord.phase = PatchPhase.GUARD_SYNTHESIS`. The
orchestrator halts the walk at the first failing phase, so
`IMPLEMENTATION`, `REGRESSION`, and `REPLAY_VERIFICATION` are never
attempted. The record's `phase_outcomes` carries three entries —
DISCOVERY (passed), RISK_PROBE (passed), GUARD_SYNTHESIS (failed) —
and stops.

---

## Fail reason

```
fail_reason = "missing_guards: at least two guards required"
```

The reason string is deterministic and machine-parseable. The
prefix `missing_guards:` is part of the protocol's published
contract; downstream tooling can branch on it.

---

## Why the benchmark was never reached

Two reasons, both deliberate:

1. **Cost discipline.** REGRESSION calls six benchmarks; one full
   call takes several seconds. The protocol places all cheap
   structural checks before any benchmark invocation so invalid
   patches are rejected at zero benchmark cost.

2. **Correctness discipline.** A patch that lacks structural
   guards has, by construction, no falsification condition for
   the benchmark to expose. Running the benchmark on a guardless
   rule would either:
   * Coincidentally pass and produce a false confidence signal,
     **or**
   * Coincidentally fail and produce no diagnostic information
     about *which* missing guard would have fixed it.

   The protocol's response — refusing to run — is the only
   information-positive outcome.

---

## Final record

```
patch_id      : pp_<sha256[:16] over fake candidate>
target_rule   : fake_rule
source_branch : feature/v2-8-fail-fixture
phase         : guard_synthesis
passed        : false
created_guards: []
touched_files : ["src/desi/logic/inference.py"]
benchmark_hash_before : ""   # never captured
benchmark_hash_after  : ""   # never captured
replay_hash   : d83d81ab8417c022
fail_reason   : "missing_guards: at least two guards required"
```

Full JSON at `artifacts/v2_8/fail_case.json`.

Every claim in this document is machine-checked by
`tests/protocol_docs/test_doc_consistency.py`.
