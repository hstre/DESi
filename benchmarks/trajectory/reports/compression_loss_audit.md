# DESi compression loss-attribution audit — DriftBench (read-only)

For each compression STEP along the pipeline `A(raw) → B(filler removed) → F(full state) → E → D → C`, attribute the tokens saved, the epistemic signal lost, and which signal family becomes invisible. Disproportionate loss is FLAGGED, never patched. Measurement-only; no DESi-core change.

## Size
- Trajectories: **1525**. Raw mean 9899.6 tokens.

## Per-step attribution (ordered by increasing compression)

| step | removes | signals lost | extra compression | epistemic loss | lost-signal weight | danger (loss / extra-compression) | flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A->B | filler / low-information turns | — | 0.0002 | 0.0 | 0.0 | 0.0 | ok |
| B->F | raw transcript text (-> structured DESi state) | — | 0.9644 | 0.0 | 0.0 | 0.0 | ok |
| F->E | lock-in proxy + recovery-quality + drift-energy + composite | lock_in | 0.0063 | 0.011 | 0.0111 | 1.746 | **FLAG** |
| E->D | recovery counts + per-turn drift/recovery event ledger | event, recovery | 0.0221 | 0.557 | 0.5571 | 25.204 | **FLAG** |
| D->C | branch entropy + branch-collapse state | branch | 0.0022 | 0.209 | 0.2089 | 95.0 | **FLAG** |
- `extra compression` = additional fraction of raw tokens removed by this step (vs. the previous variant). `epistemic loss` = drop in retained epistemic signal. `danger` = epistemic loss per unit of extra compression — high when a step destroys signal for almost no token gain. Steps with danger ≥ 0.5 (or any loss at ≤0 token gain) are flagged.

## Step-level findings

- **Saves the most tokens:** `B->F` (+0.9644 compression) — raw transcript text (-> structured DESi state).
- **Loses the most epistemic information:** `E->D` (−0.557 retained) — drops event, recovery.
- **Safest step:** `B->F` (epistemic loss 0.0, extra compression 0.9644).
- **Most dangerous step:** `D->C` (danger 95.0: loses branch for 0.0022 extra compression).

## Which step causes which specific failure

- **Branch collapse** (branch state becomes invisible): step `D->C`.
- **Recovery invisibility** (recovery events/quality gone): step `E->D`.
- **Lock-in loss** (irreversible-lock-in signal gone): step `F->E`.

## Where catastrophic epistemic degradation begins

- Catastrophic degradation begins at the first flagged step, **`F->E`**: it removes lock-in proxy + recovery-quality + drift-energy + composite — losing lock_in — while adding only 0.0063 extra compression. From there, each further strip (toward constraint-only) destroys a signal family for almost no token gain. Honest caveat: the FIRST flag (`F->E`) loses only 0.011 retained signal because the lock-in proxy barely tracks the auditor's lock-in class on DriftBench (weight ~0.01) — it trips the flag only because it saves ~0 tokens. The genuinely LARGE epistemic collapse is at **`E->D`** (−0.557 retained), where event and recovery become invisible.

## Does DESi know when its own compression becomes epistemically unsafe?

- The compact state carries per-trajectory counts that mark which fields are **load-bearing** (non-zero structure that further compression would erase):
  - branch state load-bearing (branch_collapse > 0): 1135/1525 (74%).
  - recovery/event load-bearing (events or failed-recovery > 0): 1475/1525 (97%).
  - lock-in load-bearing (lock-in proxy > 0): 1139/1525 (75%).
  - ANY component load-bearing: 1475/1525 (97%).
- **Operationally yes, structurally no:** the state's own counts identify, per trajectory, exactly which families are load-bearing — so a deterministic guard ('do not drop a field whose count > 0 for this trajectory') is derivable from the state itself. But the DESi core has no built-in alarm that fires when compression crosses into unsafe territory; that judgement lives in this external audit. (We FLAG this; we do not add such a guard — that would be a patch.)

## Verdict

- The expensive, valuable compression is **raw → full DESi state** (huge token savings, zero measured epistemic loss). Every step that shrinks the state further removes a whole signal family for negligible additional savings, so **Full DESi (F) sits at the Pareto knee** and the sub-F variants are strictly worse trades on this benchmark.
- Flagged steps: F->E, E->D, D->C — reported, NOT patched (per the audit rule).

## DESi-core invariance
- Read-only; consumes the ablation rows; core byte-identical; no metric mutation, no threshold tuning, no improvement patch.

## Honesty / limits
- Loss is attributed via the retained-signal weights from the ablation run (|corr| of each DESi field vs. a single-auditor dimension); steps that save near-zero tokens yield very large or infinite danger ratios by construction — that is the point (they are pure-loss operations), not an artifact to be smoothed. The pipeline order is fixed structurally; no label was used to choose it.
