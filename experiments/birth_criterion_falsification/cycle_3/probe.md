# Cycle 3 — Component F (Falsifiability)

## Paper 0 wording

> **F — Falsifiability**: Proposed revisions must be testable under
> adversarial conditions; the system must tolerate rejection,
> regression, and failed hypotheses.

## Strongest absence-hypothesis

Every "adversarial test" run against DESi was authored by an agent
with knowledge of DESi's existing failure modes. The n=10 DET-FAL
suite was built to probe specific known rules; the n=20 generalization
suite was authored AFTER the 12-cycle loop, with knowledge of which
rules cycles 1-11 had changed. There has been **no test against a
distribution DESi was not designed against**. F is satisfied only
in the trivial "tests exist" sense.

## Evidence in repo

- The n=10 fixtures in `data/adversarial/` correspond directly to
  enumerated rule-failure cases (T1-T10 in the DET-FAL ledger).
  Each fixture was designed to trigger one rule's known weakness.
  Test-suite-against-fixtures is in-suite by construction.
- The n=20 fixtures in `experiments/generalization_loop/generate_fixtures.py`
  have `_meta` blocks like `"why_this_is_unseen": "Cycle 2 closed Phase
  V on reversal but doesn't re-open. Lock-recovery-lock pattern is new."`
  The author (me) explicitly authored fixtures targeting *known*
  not-yet-fixed weaknesses. This is not held-out.
- `paper0/self_reflection.md` §10 — "Failure Modes That Remain" — is
  honest: it enumerates limitations including domain transfer.
- Paper 0 itself §11.10 acknowledges: "broader generalization across
  natural domains, long trajectories, and semantic complexity remains
  unestablished."

## Counter-evidence

- Paper 0's F as literally worded says *revisions must be testable*
  and *the system must tolerate rejection*. Both are documented:
  - Testable: pytest + suite metrics. Yes.
  - Tolerates rejection: self-improvement-loop cycle 2 and cycle 10
    first implementations were rejected by tests, preserved as
    documented failed attempts, then replaced with corrected
    versions. Yes.
- F is *not* defined as "tested under held-out adversarial
  distribution". A stricter reading is plausible but not in the
  paper text.

## Verdict

**F is SATISFIED under Paper 0's literal wording.** The "held-out
distribution" attack is a different (stronger) criterion than what
§12.1 states. Paper 0 §11.10 itself flags transfer-evidence as
first-order only; this is a self-acknowledged limit, not a hidden
flaw, so it doesn't force F = 0.

**Does not force birth(B) = 0.**

## Marginal epistemic gain

Non-zero. The honest reading: F holds in the weakest possible form
Paper 0's wording supports. A reasonable strengthening — "tested on
distributions the system was not designed against" — is unmet. Future
work (the n=??? real-DES-paper7 cross-validation in
`experiments/generalization_loop/final_report.md` §12 question 12.A)
would either strengthen F or force it to 0.
