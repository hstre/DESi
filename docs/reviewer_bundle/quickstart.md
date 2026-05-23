# Quickstart — Reproduce v2.7 + v2.8 + v3.1 in ≤ 15 minutes

Target: an external reviewer with a fresh clone, `python ≥ 3.10`
and `pytest` installed. No network access required, no API keys,
no GPU.

Total commands: **9**. Total expected runtime: **≤ 5 minutes** on
a typical laptop.

If any step diverges from the expected output, the reviewer
bundle has failed — please open an issue on the repository.

---

## Step 0 — One-time setup

```bash
git clone <repo-url> DESi
cd DESi
```

Expected runtime: ~30s on a normal connection.

---

## Step 1 — Verify the baseline test suite

```bash
PYTHONPATH=src pytest -q
```

Expected: all tests pass. Headline:

```
1723 passed
```

Expected runtime: ~20s.

---

## Step 2 — Reproduce v2.7 (guarded CAUSAL_CHAIN rule)

```bash
PYTHONPATH=src pytest tests/logic/test_causal_chain.py tests/logic/test_causal_chain_regression.py -q
```

Expected: all 33 v2.7 tests pass. This proves:

- `InferenceRule.CAUSAL_CHAIN` exists and fires only on linear
  chains.
- All 6 R4 contradiction cases stay blocked.
- All 6 R5 cycle cases stay blocked.
- None of the 8 known false-positive ids reopen.
- The v1.5 main benchmark precision/recall/FP are still 1.0/1.0/0.

See `reproduce_v27.md` for the per-test mapping.

---

## Step 3 — Reproduce v2.8 (rule-patch protocol)

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
print('v2.7 reconstruction replay_hash =', recon.replay_hash)
print('v2.7 phase                     =', recon.phase.value)
print('v2.8 fake-patch replay_hash    =', fake.replay_hash)
print('v2.8 fake-patch phase          =', fake.phase.value)
print('v2.8 fake-patch fail_reason    =', fake.fail_reason)
"
```

Expected output (exact, byte-for-byte):

```
v2.7 reconstruction replay_hash = 1f4d9dfe44cb16e1
v2.7 phase                     = complete
v2.8 fake-patch replay_hash    = d83d81ab8417c022
v2.8 fake-patch phase          = guard_synthesis
v2.8 fake-patch fail_reason    = missing_guards: at least two guards required
```

See `reproduce_v28.md` for the full record schema.

---

## Step 4 — Reproduce v3.1 (claim-anchor discipline)

```bash
PYTHONPATH=src pytest tests/doc_anchors/ tests/reviewer_bundle/ -q
```

Expected: all anchor + reviewer-bundle tests pass.

The headline numbers (claims RB-052..060 in `claim_index.json`):

- `self_deception_rate` dropped from 0.314 (v3.0) to **0.05144** (v3.1).
- 36/36 anchors verify against their artefacts.
- 0 hash mismatches; 0 drift findings.

See `reproduce_v31.md` for the validation flow.

---

## Step 5 — Verify the reviewer metrics

```bash
PYTHONPATH=src python -m json.tool artifacts/v3_2/reviewer_metrics.json
```

Expected: a JSON document whose fields (claims RB-061..067 in
`claim_index.json`) satisfy:

- `total_claims >= 50`
- `verified_claims == total_claims`
- `commands_required <= 15`
- `estimated_minutes <= 15`
- `broken_links == 0`
- `missing_paths == 0`
- `hash_mismatches == 0`

---

## Command count

| Step | Commands | Cumulative |
| --- | ---: | ---: |
| Step 0 (clone + cd) | 2 | 2 |
| Step 1 (full suite) | 1 | 3 |
| Step 2 (v2.7) | 1 | 4 |
| Step 3 (v2.8) | 1 | 5 |
| Step 4 (v3.1) | 1 | 6 |
| Step 5 (metrics) | 1 | 7 |

**Total: 7 commands.** Under the 15-command budget.

## What if any step fails?

* **Step 1 fails** → the baseline is broken; the reviewer bundle is
  not at fault.
* **Step 2 fails** → either the v2.7 rule, its guards, or a
  regression test has drifted. Open `tests/logic/test_causal_chain*.py`
  for the offending assertion.
* **Step 3 prints a different hash** → the protocol orchestrator's
  determinism broke. Compare `artifacts/v2_8/reconstruction.json`
  vs `artifacts/v2_8/fail_case.json` for the source of drift.
* **Step 4 fails on `test_corpus_anchors`** → a documentation
  anchor disagrees with its artefact. The test prints the doc
  path, line number, and the conflicting value.
* **Step 5 shows out-of-budget metrics** → either the reviewer
  bundle has bloated past 15 commands / 15 minutes, or
  `artifacts/v3_2/reviewer_metrics.json` has drifted from its
  expected schema.
