# Cycle 1 — Component D (Failure Detection)

## Paper 0 wording

> **D — Failure Detection**: The system must detect failures in its own
> diagnostic rules, not merely task failures or external criticism.

## Strongest absence-hypothesis

DESi's "self-detection" is not architecturally separate from the system
being diagnosed. The actual detection events in the corpus are:

- `paper0/self_reflection.md` (§§1–7) — DESi attacks DESi. **Authored
  by a single LLM (Claude) with a DESi-prefix prompt.**
- Per-cycle "next-cycle hint" chains in
  `experiments/self_improvement/cycle_N/evaluation.md` and
  `experiments/generalization_loop/cycle_N/evaluation.md`. **Authored
  by the same LLM in conversation.**
- Pytest failures, suite-metric deltas, and `compute_all` outputs.
  These are **mechanical** — they execute the rules; they do not
  detect failures in them.

If "the system" means the deterministic Python in `src/desi/`, then
the deterministic system **does not detect failures in its own rules**;
it only executes them. The detection happens elsewhere — in an LLM
running with a prefix saying it is DESi. Whether "Claude with a
DESi prefix" is the same epistemic subject as the Python code is an
open question Paper 0 does not formally address.

## Evidence in repo

- `paper0/self_reflection.md` exists; authored in an LLM turn,
  no separation between the model doing the critique and the model
  doing other DESi roles. Same context window can produce both
  "trajectory analyst" output and "skeptical auditor" output.
- `src/desi/diagnostics.py` and `src/desi/phase_detector.py` contain
  zero self-introspection logic. They compute classifications and
  spans; they do not flag "this rule may be wrong".
- The auditor-model ablation (`paper0/run_auditor_ablation.py`) shows
  the auditor is one of the *same* LLM family with different model
  weights — not an architecturally separate detector.

## Counter-evidence

- The pytest suite IS a separate detector: it flags concrete rule
  regressions. Self-improvement-loop cycle 2 and cycle 10's first
  implementations were both caught by pytest before commit, then
  documented as failed attempts. That is "the system detecting
  failures in its own rules" if you count tests-as-rules.
- Suite metrics (DET-FAL ledger, attractor_lock fire counts,
  phase_overlaps) are mechanical detectors of rule misbehavior.
  They DO surface failures (e.g. n=20 baseline's attractor_lock 20/20
  surfaced an over-permissive rule).

## Verdict

**D is WEAKLY SATISFIED**, not absent. Pytest + suite-metric mechanics
satisfy D in the literal sense. The architectural complaint —
"the LLM doing the critique is the LLM running the prompts" — is real
but does not force D = 0 under Paper 0's wording: §12.1 says the
system must *detect* failures, not that the detector must be
architecturally distinct.

**Does not force birth(B) = 0.**

## Marginal epistemic gain

Non-zero but small. The D-as-architectural-separation reading is a
stronger criterion Paper 0 could have stated but did not. Future
Paper-0 revision could tighten the definition. Recorded as
*observation*, not falsification.
