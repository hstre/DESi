# Cycle 8 — switch penultimate-EN to composite classifier

Self-diagnosis: paper0/self_reflection.md §3 + cycle-7 hint. DET-FAL
T6 (adv06): penultimate EN has high ENI but no recovery; legacy
classifier labels it "genuine_transformation" so the principle fires
`has_candidate=True` falsely.

## Change

`detect_penultimate_en_candidate` now consumes
`classify_en_events_composite` (cycle 7). Candidate iff penultimate
== `genuine_transformation_confirmed` AND last !=
`genuine_transformation_confirmed`.

## Target

DET-FAL T6.

## Expected metric

- adv06 `has_candidate`: True → False. DET-FAL FP 2 → 1.
- 25 → 26 pytest cases.

## Risk

Low. One detector body change. No prompt change.
