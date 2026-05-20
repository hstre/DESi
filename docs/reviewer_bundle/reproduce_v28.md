# Reproduce v2.8 — Rule Patch Protocol

v2.8 extracted the v2.7 process into a closed seven-phase protocol
that can be replayed against the historic patch (positive control)
and against a deliberately-invalid candidate (negative control).

## The minimal reproduction

```bash
PYTHONPATH=src python -c "
from desi.rule_patch_protocol import (
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)
proto = RulePatchProtocol()
recon = proto.run(causal_chain_v2_7_candidate())
fake  = proto.run(fake_rule_without_guards_candidate())
print('recon.replay_hash =', recon.replay_hash)
print('recon.phase       =', recon.phase.value)
print('recon.passed      =', recon.passed)
print('recon.guards      =', len(recon.created_guards))
print('fake.replay_hash  =', fake.replay_hash)
print('fake.phase        =', fake.phase.value)
print('fake.fail_reason  =', fake.fail_reason)
"
```

Expected output (exact):

```
recon.replay_hash = 1f4d9dfe44cb16e1
recon.phase       = complete
recon.passed      = True
recon.guards      = 7
fake.replay_hash  = d83d81ab8417c022
fake.phase        = guard_synthesis
fake.fail_reason  = missing_guards: at least two guards required
```

## What the seven phases do

| # | Phase | Failure condition |
| -: | --- | --- |
| 1 | DISCOVERY | a declared `required_artifact` does not exist on disk |
| 2 | RISK_PROBE | `known_false_positive_reopen_rate != 0.0`, or authority/philosophy touch, or `safe_to_implement != true` |
| 3 | GUARD_SYNTHESIS | `len(guards) < 2`, or any `observable` outside the closed allowlist, or any `observable` contains `case_id` / `allowlist` |
| 4 | IMPLEMENTATION | a declared `touched_file` is missing or outside allowed roots |
| 5 | REGRESSION | any of the six benchmark hashes differs from baseline |
| 6 | REPLAY_VERIFICATION | two consecutive runs disagree on any hash |
| 7 | COMPLETE | terminal sentinel; reached only when all six predecessors pass |

## The two canonical fixtures

`causal_chain_v2_7_candidate()` re-encodes the v2.7 patch as a
`PatchCandidate`: 7 guards, 8 touched files, 3 required
artefacts. The protocol replays it and reaches
`phase=complete` with replay_hash `1f4d9dfe44cb16e1`.

`fake_rule_without_guards_candidate()` declares zero guards. The
protocol rejects it at GUARD_SYNTHESIS with `fail_reason =
"missing_guards: at least two guards required"`, replay_hash
`d83d81ab8417c022`.

## Anchored claims

| Claim | Statement | Artefact | Field | Expected |
| --- | --- | --- | --- | --- |
| RB-042 | reconstruction reaches phase=complete | `artifacts/v2_8/reconstruction.json` | `phase` | `complete` |
| RB-043 | reconstruction passed flag is true | `artifacts/v2_8/reconstruction.json` | `passed` | `true` |
| RB-044 | reconstruction declares 7 guards | `artifacts/v2_8/reconstruction.json` | `len:created_guards` | `7` |
| RB-045 | reconstruction declares 8 touched files | `artifacts/v2_8/reconstruction.json` | `len:touched_files` | `8` |
| RB-046 | reconstruction `benchmark_hash_before == _after` | `artifacts/v2_8/reconstruction.json` | `benchmark_hash_before==benchmark_hash_after` | `true` |
| RB-047 | reconstruction fail_reason is empty | `artifacts/v2_8/reconstruction.json` | `fail_reason` | `""` |
| RB-048 | fake-case stops at guard_synthesis | `artifacts/v2_8/fail_case.json` | `phase` | `guard_synthesis` |
| RB-049 | fake-case passed flag is false | `artifacts/v2_8/fail_case.json` | `passed` | `false` |
| RB-050 | fake-case fail_reason starts with missing_guards | `artifacts/v2_8/fail_case.json` | `startswith:fail_reason` | `missing_guards` |
| RB-051 | fake-case declares zero guards | `artifacts/v2_8/fail_case.json` | `len:created_guards` | `0` |

Verified by `tests/reviewer_bundle/test_claim_index.py::
test_each_claim_value_matches_artifact[RB-042..051]`.
