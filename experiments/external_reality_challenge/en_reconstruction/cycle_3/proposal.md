# Cycle 3 — Native-DES operation taxonomy report

## Stance

Documentation-only. **No new detectors added** to `src/desi/`. This
cycle classifies every entry of the upstream DES `operation_history`
into one of five categories and reports coverage. The classifier is
a small analysis script that calls the existing
`parse_des_operation` plus the cycle-1 / cycle-2 reconstruction
rules. No DESi behaviour changes.

## Taxonomy

```
reconstructed_EN_candidate
    parse succeeded AND sub_role == "hypothesis_builder" AND target is not None
    → cycle-1 rule fires; counted in m.en_reconstruction

reconstructed_critique_navigation_candidate
    parse succeeded AND sub_role == "falsifier" AND target is not None
    → cycle-2 rule fires; counted in m.critique_navigation

plain_operator_transition
    parse succeeded AND sub_role is None AND target is None
    → bare "Tn on Cxxx"; DES manipulated an existing claim without
      explicit role annotation or graph extension

unsupported_extension
    parse succeeded AND (
        (sub_role is not None AND sub_role not in {hypothesis_builder, falsifier})
        OR
        (sub_role is None AND target is not None)
    )
    → recognised but does not match a current reconstruction rule;
      future cycles can decide whether to add a rule

unparsed_operation
    parse_des_operation returned OperatorParseFailure
    → token shape not recognised at all; DESi sees OPERATOR_PARSE_FAILURE
```

The five categories partition `operation_history` (each op falls
into exactly one). Two coverage questions:

1. **Coverage** — fraction of operations that fall into a
   reconstruction category (EN or critique-nav). Higher = DESi sees
   more of DES's graph-extending work.
2. **Target-creating completeness** — of operations where the parser
   reported a target_claim, do ALL of them land in either EN or
   critique-nav? If any target-creating op falls into
   `unsupported_extension`, there's a structural extension DESi is
   refusing to classify.

## What this cycle does NOT change

- No new file in `src/desi/`.
- No new field on any model or DeterministicMetrics dataclass.
- No new test in `tests/`.
- Existing pytest suite (58) must continue to pass.
- n=10 + n=20 suites: unaffected (no detectors change).
- External DES probe (conservative + heuristic): unaffected.

## Deliverables

- `taxonomy.py` — the analyser script.
- `taxonomy_report.md` — output table + summary.
- `evaluation.md` — interpretation.

## Stop condition

This cycle is intrinsically one-shot. After the taxonomy is
computed and the four measurements are recorded, stop.
