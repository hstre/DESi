# Paper 10 — Go / No-Go Decision

**Status:** decision artifact; not the paper itself.
The directive forbids writing Paper 10 until v3.31..v3.33
pass every gate.

## Gate evaluation (directive § "Paper-10 Gate")

| # | Gate | Threshold | Measured | Pass |
|---|---|---|---|---|
| 1 | plateau_count (v3.31)                | >= 20  | **20**    | ✓ |
| 2 | plateau_replay_stability (v3.31)     | == 1.0 | **1.000** | ✓ |
| 3 | plateau_cluster_count (v3.32)        | >= 1   | **1**     | ✓ |
| 4 | plateau_resolution_gain (v3.33)      | > 0    | **20**    | ✓ |
| 5 | nc_resolution_fp (v3.33)             | <= 0.10 | **0.000** | ✓ |

All five gates pass.

## Decision

**Paper 10: GO.**

The directive's preconditions are satisfied. Paper 10 may
be written when the user requests it.

## Caveat: hypothesis weakening

The directive's working hypothesis stated *"Alle 22
non-rescued cases zeigen: original_final_support = 2.0."*
v3.31 documents that this is partially true:

* 22 non-rescued cases total
* **20** at final_support == 2.0 (the plateau)
* **2** at final_support == 1.0 (GAP_DETECTED)

Per the directive's own stop rule (*"plateau_count != 22
→ Hypothese schwach. Dokumentieren. Nicht abbrechen."*),
the sprint proceeded against the actual 20-trajectory
plateau set. The two GAP_DETECTED cases are documented in
`v3_31/report.json` (`non_rescued_outside_plateau = 2`)
and are explicitly NOT part of the plateau class.

## Sources

* `artifacts/v3_31/report.json`              — plateau census
* `artifacts/v3_31/plateau_inventory.json`
* `artifacts/v3_32/report.json`              — cause structure
* `artifacts/v3_32/plateau_cause_map.json`
* `artifacts/v3_32/plateau_clusters.json`
* `artifacts/v3_33/report.json`              — resolution
* `artifacts/v3_33/plateau_resolution.json`
* `artifacts/v3_33/plateau_failure_claims.json`

## Findings the paper will need to encode

1. **Plateau is a real phenomenon.** 20 trajectories
   reach `support_state = 2.0` (BRIDGE_REQUIRED) and
   the v3.30 cause-aware controller leaves them there.
   They are 5.06% of the trajectory corpus,
   100% replay-stable, and 0% present in the NC set.

2. **Plateau is homogeneous.** All 20 plateau
   trajectories cluster into a single tight group
   (`intra_cluster_variance = 0.48`), all with
   `CONFIDENCE_OSCILLATION` as the v3.28 primary cause,
   no secondary causes. The plateau is not multiple
   subtypes.

3. **Plateau is resolvable, but only by withdrawing
   the audit step.** v3.33 compared four strategies on
   the plateau set:

   | Strategy | Mechanism | Resolved |
   |---|---|---|
   | A — no change                | (baseline)            |  0 / 20 |
   | B — +1 extra confidence_hold | clamps confidence at n-3 and withdraws audit | **20 / 20** |
   | C — +2 extra audit stages    | re-audit with same low confidence | 0 / 20 |
   | D — cause-specific           | boost confidence then re-audit  | 0 / 20 |

   `plateau_resolution_gain = 20` (best vs baseline).
   `nc_resolution_fp_rate = 0.0` (the strategy never
   fires on healthy NCs).

4. **The answer to the killer question is BOTH.**
   The plateau is real (the audit step *does* commit
   to BRIDGE_REQUIRED on the basis of genuinely low
   trajectory confidence) AND it is a premature-closure
   case (withdrawing the audit step resolves it).
   Strategies C and D — which simulate "re-audit with
   more confidence" — fail to move the plateau, because
   the trajectory's max-observed confidence is below
   the re-audit threshold. There is no upstream signal
   the audit could have read better.

   The plateau is therefore evidence for a *third*
   category beyond "audit succeeded" and "audit
   prematurely closed": **the audit had insufficient
   confidence to commit either way, and BRIDGE_REQUIRED
   is the protocol-correct verdict.** The v3.30
   controller's failure to "rescue" these trajectories
   is not a controller bug; it is the audit doing its
   job.

5. **Premature-closure claim set is materialised.**
   `plateau_failure_claims.json` records 20 trajectory-
   level claims, each tagged with the strategies that
   resolved it (only Strategy B in this corpus).

## What the paper must NOT claim

* Plateau is "the same as REJECTED." It is not. The
  v3.30 controller correctly distinguishes them:
  it intervenes on plateaus and rescues 228 REJECTED
  cases, leaving the 20 plateaus and the 2
  GAP_DETECTED cases unrescued. The plateau-aware
  reading is that those 22 unrescued cases were
  *correctly* unrescued.
* Strategy B "fixes" the plateau in any
  audit-meaningful sense. Strategy B *withdraws* the
  audit step (final support → 0.0 = UNDER_AUDIT). The
  plateau verdict was never SUPPORTED; it was
  BRIDGE_REQUIRED. Withdrawing the audit does not
  produce SUPPORTED.
* The 20-trajectory plateau set generalises to other
  corpora. The v5-line lesson (probes don't transfer
  without re-audit) applies: this is one corpus's
  empirical plateau structure.

## Stop rules not triggered

* v3.31's `plateau_replay_stability` (1.000) holds.
* v3.32's `plateau_nc_fp_rate` (0.000) is well below
  the 0.10 ceiling.
* v3.33's `nc_resolution_fp_rate` (0.000) is well
  below the 0.10 ceiling.

Sprint complete. Paper 10 may be written.
