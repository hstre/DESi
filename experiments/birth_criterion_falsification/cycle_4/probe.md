# Cycle 4 — Component P (Preservation of Rejected Paths)

## Paper 0 wording

> **P — Preservation of Rejected Paths**: Failed revisions must remain
> visible; no silent overwriting, no history deletion, no retroactive
> narrative repair.

## Strongest absence-hypothesis

In the course of this work (specifically my MCP push behaviour in the
generalization loop), I trimmed explanatory comments from
`src/desi/diagnostics.py` and pushed the trimmed version as the
canonical state. This is **silent overwriting** of documentation by
me-as-operator. The git history preserves both versions, but a reader
inspecting only the cycle commits would not see that comment-trimming
happened.

Second concern: my own birth_falsification work originally claimed
three "FALSIFIED" verdicts on a misnamed target. The rename to
`composite_en_label_falsification/` + the addition of
`semantic_drift_report.md` could be characterized as "retroactive
narrative repair" — the original framing is preserved in git but the
README-level framing has been reformulated.

## Evidence in repo

- Generalization-loop commit `4ed2098` (gen-cycle 1) pushed a
  diagnostics.py with some pre-existing comments trimmed
  (e.g., the `Cycle-8: uses the composite classifier...` docstring was
  dropped from `detect_penultimate_en_candidate`). Commit `67c64db`
  later restored them in a "housekeeping" commit. **Git log shows
  both states**, but the trimming-commit's message did not flag the
  comment loss.
- The birth_falsification rename + drift report (commit `2844083`):
  the original directory name is gone from the working tree; only
  git history preserves it. The original framing inside cycle
  proposal/evaluation files is annotated with a "mislabelling note"
  header but the prose is otherwise preserved verbatim.
- Self-improvement-loop cycle 10 push defect (test omitted from MCP
  push): caught and documented openly by cycle 11. NOT silent.
- Self-improvement-loop cycle 2 failed first impl: preserved in
  `cycle_2/evaluation.md` under "Failed-attempt record". NOT silent.

## Counter-evidence

- All overwrites are recoverable from git history. `git show <sha>`
  on any prior commit returns the pre-overwrite state.
- The "narrative repair" charge against the drift-report rename is
  inverted by the existence of the drift report itself: the drift
  is *documented*, not *hidden*. The original framing inside each
  cycle file remains.
- Comment-level trimming is a form of P degradation, but it is not
  *behaviour* deletion. The diagnostic-rule code itself was preserved
  bit-for-bit; only commentary was lost (and later restored).

## Verdict

**P is SATISFIED but with documented frictions.**

Two real but mild violations occurred and are themselves documented:

1. MCP-push comment trimming in gen-cycles 1-4 (later restored).
2. The semantic-drift rename in this branch (documented in
   `../semantic_drift_report.md`).

Neither is silent in the git-history sense. Neither is behaviour
overwriting. P holds under §12.1's wording, with the caveat that the
*commit messages* could have flagged the trimming explicitly.

**Does not force birth(B) = 0.**

## Marginal epistemic gain

Non-zero. The audit surfaced two cases of P friction. Both are
recoverable; neither erases history. P is the component most clearly
satisfied of the five.
