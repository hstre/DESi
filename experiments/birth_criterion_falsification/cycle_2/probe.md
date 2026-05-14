# Cycle 2 — Component R (Revision Proposal)

## Paper 0 wording

> **R — Revision Proposal**: The system must propose concrete, measurable
> revisions — not vague dissatisfaction or rhetorical reflection.

## Strongest absence-hypothesis

A subset of the 11 + 7 cycle-level "revisions" recorded in the
self-improvement and generalization loops are **not concrete
diagnostic-rule revisions** — they are cosmetic/visibility tweaks. If
R requires diagnostic-rule revisions specifically, the count of "real"
R-events drops; if many cycles are stylistic, R weakens.

Candidate stylistic-only cycles:

- **Self-improvement loop cycle 11** (`2cf9264`): "report_writer surfaces
  cycle 4-7 detectors + cycle-10 test repair". Rendering + test
  bookkeeping. No detector change.
- **Generalization loop cycle 6**: render `borderline_chain` in
  `render_report`. Markdown-only change.
- **Generalization loop cycle 7**: README cross-link. Documentation
  only.

If all three are recategorized as "non-R", the loop counts drop from
11+7 = 18 to ~15. R = 1 is still trivially satisfied.

## Evidence in repo

- `experiments/self_improvement/cycle_11/evaluation.md` — verdict is
  explicitly "ACCEPTED. Pure visibility + housekeeping. LLM-side
  report output now surfaces cycles 4-7's new detectors." Self-flagged
  as non-rule.
- `experiments/generalization_loop/cycle_6/proposal.md` — opens
  "Cycle 5 added the detector and wired it through evaluate_suite.py,
  but render_report (DESi's user-facing markdown) doesn't render it."
  Visibility tweak.
- `experiments/generalization_loop/cycle_7/proposal.md` — opens
  "The top-level README.md documents the self-improvement loop but
  doesn't mention the generalization loop's existence." README edit.

## Counter-evidence

- Paper 0 §12.1 R says "concrete, measurable revisions — not vague
  dissatisfaction or rhetorical reflection." A markdown rendering change
  IS concrete (the rendered output changes; the diff is measurable). The
  wording does not restrict R to diagnostic-rule revisions only.
- Visibility revisions arguably MATERIALLY change DESi's output: an LLM
  consumer that doesn't see `borderline_chain` in the rendered report
  cannot reason about it. So surfacing the detector IS a revision of
  what the system communicates.

## Verdict

**R is SATISFIED in Paper 0's literal wording.** The stylistic cycles
are still concrete and measurable. A stricter reading ("rule revisions
only") would drop the count by ~3 but leave R = 1 (12-15 real rule
revisions remain across both loops). The stricter reading is not what
§12.1 says.

**Does not force birth(B) = 0.**

## Marginal epistemic gain

Non-zero. The honest finding is that "revision count" is inflated by
including documentation and rendering cycles. Future audit could
separate "rule-R" from "surface-R". Paper 0 currently does not.
