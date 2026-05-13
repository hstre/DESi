# Cycle 10 — Phase III first-trigger on composite EN classifier

Self-diagnosis (cycle-7 follow-through): Phase III's first-genuine
trigger used the legacy bimodal classifier. A high-ENI EN that
produced no downstream recovery could still trigger Phase III.

## Change

`detect_phase_iii` now uses `classify_en_event_composite` for the
**first-genuine** trigger (must be `genuine_transformation_confirmed`).
The **window-boundary** lookup intentionally stays on legacy
`classify_en_event` — any high-ENI event bounds the recovery window.

## Failed-attempt record (strict rule 4)

First implementation switched both lookups to composite. On adv06
the next EN (unconfirmed) no longer bounded the window, extending
Phase III from 2..2 to 2..6 and overlapping Phase V (4..6). Reverted
the boundary to legacy before commit.

## Files

- `src/desi/phase_detector.py` (detect_phase_iii body)
- `tests/test_phase_detector.py` (new regression)
- `experiments/self_improvement/cycle_10/*.md`
- `README.md`
