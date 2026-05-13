# Cycle 2 — Clip earlier phase spans where a later phase has already started

## DESi self-diagnosis (from cycle 1 + baseline)

Both suites still show overlapping phase spans:

- n=20: 5/20 fixtures (gen03, gen07, gen10, gen13, gen14).
- n=10: 3/10 fixtures (adv03, adv06, adv09).

The 11 cycles of the prior loop never targeted overlap-elimination, so
this is a real generalization-test signal: the phase detectors are
INDEPENDENT and don't reconcile their spans.

## Change (orchestration-layer post-processor — strict rule 1 honoured)

`detect_phases` gains a post-processing pass `_clip_phase_overlaps`:
when an earlier phase span overlaps with a later one (PHASES_ORDERED),
clip the earlier's end_loop to (later.start - 1). Drop spans that
become empty. The 'winner' on overlap is always the later phase in
the ordered tuple (I → II → III → IV → V).

No individual phase detector is modified.

## Predicted impact

- n=20 phase overlaps: 5 → 0.
- n=10 phase overlaps: 3 → 0.
- No DET-FAL counter change expected.
- Two new regression tests.
