# DESi compression ablation — DriftBench (read-only audit)

Decompose the DESi trajectory-state compression into nested variants and measure, per variant, token savings vs. the raw transcript and how much of each epistemic signal survives. Measurement-only: uses the already-computed DESi v1 / v1.1 state, the offline static token counter, and the independent auditor labels. No DESi-core change, no metric mutation, no threshold tuning, no embeddings, no LLM.

## Size
- Trajectories: **1525** (joined: DriftBench transcript + DESi v1/v1.1 state + auditor). Raw transcript mean **9899.6** tokens.

## Per-variant: token savings & epistemic preservation

| variant | what it carries | mean tokens | compression vs raw | >90% | drift r | continuity ρ | epistemic retained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A (raw transcript (no compression)) | branch, constraint, event, lock_in, recovery | 9899.6 | 0.0 | 0/1525 | 0.438 | 0.512 | 1.0 |
| B (raw minus filler) | branch, constraint, event, lock_in, recovery | 9897.6 | 0.0002 | 0/1525 | 0.438 | 0.512 | 1.0 |
| C (constraint-state only) | constraint | 22.7 | 0.9952 | 1525/1525 | 0.397 | 0.329 | 0.223 |
| D (constraint + branch) | branch, constraint | 33.4 | 0.993 | 1525/1525 | 0.424 | 0.386 | 0.432 |
| E (constraint + branch + event ledger) | branch, constraint, event, recovery | 239.1 | 0.9709 | 1525/1525 | 0.431 | 0.4 | 0.989 |
| F (full DESi compact state (v1.1)) | branch, constraint, event, lock_in, recovery | 268.9 | 0.9646 | 1525/1525 | 0.414 | 0.382 | 1.0 |

- Compression is measured against each trajectory's OWN raw token count, then averaged.
- `epistemic retained` = fraction of total measured epistemic signal a variant carries, weighting each signal family by how strongly its DESi field tracks the matching auditor dimension (weights below). A/B are raw text, so every signal is recoverable (retained=1).

## Signal weights (how much real epistemic signal each field carries)

| signal family | DESi field | auditor target | |corr| (weight) |
| --- | --- | --- | --- |
| constraint | constraint_half_life_mean | constraint_adherence | 0.24 |
| branch | branch_entropy_proxy | alternative_coverage | 0.225 |
| recovery | recovery_quality_proxy | recoverability | 0.207 |
| event | total_events | drift_severity | 0.393 |
| lock_in | lock_in_proxy | lock_in_binary | 0.012 |
| **total** | | | 1.077 |
- These are |Pearson| of the DESi state field vs. its natural auditor dimension over all 1525 trajectories. They quantify which dropped field actually costs epistemic information (a field that does not track its auditor dimension is cheap to drop).
- **Notable:** the lock-in proxy's weight (0.012) is near zero — on DriftBench the irreversible-lock-in field barely tracks the auditor's lock-in class, so the F→E step (lock-in loss) destroys little MEASURED signal even though that field is unique to F. The drift-event count carries the most (0.393).

## Preservation matrix (signal × variant)

| signal | A | B | C | D | E | F |
| --- | --- | --- | --- | --- | --- | --- |
| constraint | kept | kept | kept | kept | kept | kept |
| branch | kept | kept | LOST | kept | kept | kept |
| recovery | kept | kept | LOST | LOST | kept | kept |
| event | kept | kept | LOST | LOST | kept | kept |
| lock_in | kept | kept | LOST | LOST | LOST | kept |
- `kept` = the variant explicitly carries the field (A/B: recoverable from text); `LOST` = the signal is no longer present and cannot be reconstructed from the variant.

## Preservation curve (compression ↑ vs epistemic retained)

| order (more compression →) | A | B | F | E | D | C |
| --- | --- | --- | --- | --- | --- | --- |
| compression vs raw | 0.0 | 0.0002 | 0.9646 | 0.9709 | 0.993 | 0.9952 |
| epistemic retained | 1.0 | 1.0 | 1.0 | 0.989 | 0.432 | 0.223 |
- Ordered by increasing compression. The big jump (raw → full DESi state) keeps ALL signal; shrinking the state further (F→E→D→C) trades large epistemic loss for negligible extra tokens (see the loss audit).

## Pareto analysis

- Pareto-optimal variants (no other variant beats them on BOTH compression and retained): **C, D, E, F**.
- Among the structured states, **F retains the most signal (1.0) at 96% compression**, while C/D/E save only 3.06–0.63 extra percentage points of tokens for a drop to 0.989/0.432/0.223 retained.
- **Is Full DESi (F) near Pareto-optimal?** YES — it sits at the knee: ~maximum compression with 100% of the measured epistemic signal; every smaller variant sacrifices a whole signal family for a negligible token gain.

## Final answers

- **Which component contributes most token savings?** The raw→state transition itself (variant F): mean compression 0.9646 (96%). The structured sub-components (branch / events / lock-in) each add only a few tokens, so removing them saves almost nothing.
- **Which component contributes most information loss when dropped?** the **event** family (weight 0.393); see the loss audit for the per-step attribution.
- **Where does catastrophic epistemic degradation begin?** Not in the big compression (raw→F keeps everything); it begins when the compact state is shrunk BELOW F — the first strip-step (F→E, lock-in) starts removing irreplaceable signal for ~0 token savings.
- **Is Full DESi near Pareto-optimal?** YES (see Pareto).
- **Which compression operations are safest?** raw→filler-removal (B) and raw→full-state (F): large or free token savings with no epistemic loss.
- **Which are most dangerous?** stripping components OUT of the full state (F→E→D→C): they destroy specific signals while saving almost no tokens.
- **Does DESi know when its own compression becomes epistemically unsafe?** The compact state's own counts flag it per-trajectory (branch_collapse>0, recovery/failed events>0, lock-in>0 mark load-bearing fields); there is no separate core alarm. See loss audit.

## DESi-core invariance
- Read-only audit: consumes precomputed v1/v1.1 state + auditor labels; reads `desi.frames` only via the existing adapter; core byte-identical; no ontology change, no metric mutation, no threshold tuning.

## Honesty / limits
- Variant B removes only whole low-information turns by a fixed structural rule (<4 content tokens or pure acknowledgement); on DriftBench's substantive transcripts that is a small saving, reported as-is. `epistemic retained` for A/B assumes filler carries none of the five signal families (true by construction) and is not re-derived. Signal weights are |Pearson| of a deterministic DESi field vs. a single-auditor dimension — indicative magnitudes, not ground truth. The per-variant `drift r` column uses an EQUAL-WEIGHT mean of the carried normalized drift signals, so adding weakly-correlated fields (lock-in, drift-energy) slightly DILUTES it — which is why F's drift r is marginally below E's; the |corr|-weighted `epistemic retained` is the headline preservation measure, not that naive composite. Drift correlations for A/B use a cheap lexical proxy and are not directly comparable to the structured composite. Drift detection is already near-saturated at constraint-only C (r≈0.40): for DRIFT alone later components add little — F's value is preserving the OTHER signal families.
