# Cycle 10 evaluation — Phase III on composite EN

pytest 27 → **28**.

## Metrics (n=10 adversarial)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| `false_positive_count` (DET-FAL) | 0 | 0 | 0 |
| `false_negative_count` (DET-FAL) | 2 | 2 | 0 |
| Phase III spans changed | n/a | 0 (adv06 preserved 2..2 by legacy-boundary exception) | — |

## Failed-attempt record

First impl switched both first-trigger and window-boundary lookups
to composite. adv06 Phase III extended to loops 2..6, overlapping
Phase V (4..6) — re-introducing the T9-shape FP cycle 2 resolved.
Reverted boundary lookup to legacy before commit. Preserved in
proposal per strict rule 4.

## Verdict

**ACCEPTED** (defensive). No DET-FAL movement; defensive guarantee
added: high-ENI-no-recovery ENs no longer trigger Phase III.

## Next cycle hint

Cycle 11: surface the new diagnostic fields
(`branch_explosion`, `mild_stagnation`, `step_coherence`,
`en_classifications_composite`) in `report_writer.py` so they appear
in the markdown report output.
