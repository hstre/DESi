# Cycle 6 — Surface `borderline_chain` in `render_report`

## Self-diagnosis

Cycle 5 added the detector and wired it through `evaluate_suite.py`, but
`render_report` (DESi's user-facing markdown) doesn't render it.

## Change

Add one line in the "New deterministic detectors" section of
`render_report` showing the borderline_chain detected flag, longest_run,
and note.
