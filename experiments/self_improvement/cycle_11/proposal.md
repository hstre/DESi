# Cycle 11 — surface new diagnostic fields in report_writer

Self-diagnosis (cycle-10 hint): the cycle 4-7 detectors
(`branch_explosion`, `mild_stagnation`, `step_coherence`,
`en_classifications_composite`) are computed but not rendered in the
markdown report.

## Change

`render_report` gains a new section
`## New deterministic detectors (cycles 4-7)` inserted between
Penultimate-EN and Attractor sections. Renders all four new
diagnostic fields.

Also restores the cycle-10 regression test
`test_phase_iii_requires_confirmed_genuine_en_after_cycle_10` which
was omitted from cycle-10's MCP push by accident.

## Verdict

No DET-FAL counter movement. Pure visibility + cycle-10 test-suite
repair. Tests 27 → 28.
