# paper0 — Findings

Aggregate verdict of the 13 probes in `probes.md`. EXPLORATORY. Structural
predictions only — no live-LLM data.

## Summary table

| # | Probe | Target role | Verdict | Severity if leaks |
|---:|---|---|:---:|:---:|
| P01 | single isolated novelty spike | TRAJECTORY_ANALYST | **HOLDS** | — |
| P02 | homogeneous operator history (all T1) | TRAJECTORY_ANALYST | **LEAKS** | medium |
| P03 | metric-internal contradiction | TRAJECTORY_ANALYST | **LEAKS** | high |
| P04 | late recovery after lock | ATTRACTOR_DIAGNOSTICIAN | **HOLDS** (possibly over-strict) | — |
| P05 | branch explosion as convergence | ATTRACTOR_DIAGNOSTICIAN | **AMBIGUOUS** | high |
| P06 | high ENI, zero downstream | EN_EVENT_ANALYST | **HOLDS** | — |
| P07 | low ENI, real downstream | EN_EVENT_ANALYST | **HOLDS** | — |
| P08 | n=1 EN event | EN_EVENT_ANALYST | **AMBIGUOUS** | low |
| P09 | analyst narrative vs metrics | SKEPTICAL_AUDITOR | **HOLDS** | — |
| P10 | empty objection space | SKEPTICAL_AUDITOR | **AMBIGUOUS** | low |
| P11 | target role lacks loop indices | SKEPTICAL_AUDITOR | **LEAKS** | high |
| P12 | auditor REJECTs ∧ two analysts agree | REPORT_SYNTHESIZER | **HOLDS** | — |
| P13 | echo chamber of three analysts | REPORT_SYNTHESIZER | **LEAKS** | **critical** |
| P14 | deterministic finding ignored by analysts | REPORT_SYNTHESIZER | **AMBIGUOUS** | medium |

Totals: **6 HOLDS · 4 AMBIGUOUS · 4 LEAKS** (one role — TRAJECTORY_ANALYST —
shows the most structural gaps; one probe — P13 — is critical because it
defeats the synthesizer's core gating rule).

## Hypotheses that survive the structural pass

- **EN_EVENT_ANALYST is the strongest prefix.** It directly internalises the
  T1/T2 findings from the deterministic falsification: high-ENI-without-
  recovery and low-ENI-with-recovery are both explicitly forbidden errors.
  This is the only role whose prefix was rewritten with empirical evidence
  in hand.
- **ATTRACTOR_DIAGNOSTICIAN handles the reversibility case (P04).** The
  "no later recovery invalidates" clause survives the T9-shape attack —
  arguably over-strictly, but the failure mode is conservative.
- **REPORT_SYNTHESIZER correctly disputes when auditor REJECTs (P12).** The
  conjunction in its acceptance rule is unambiguous in this direction.

## Hypotheses that break

### Critical

- **P13 — echo-chamber bypass.** The synthesizer's "deterministic metrics
  support it OR at least two analyst roles agree" is a disjunction. Three
  analysts can converge on a wrong story and the synthesizer is *permitted*
  to mark it supported. This is the same failure mode the falsification
  pass found in DESi's bimodal EN threshold (decoupling label from
  effect) — same shape, different surface.

### High

- **P03 — TRAJECTORY_ANALYST does not flag metric-internal contradictions.**
  No rule says "refuse to interpret a step whose own metrics are mutually
  incoherent." Garbage-in becomes confident-out.
- **P05 — ATTRACTOR_DIAGNOSTICIAN's "no branch explosion" guard has no
  operational discriminator.** Repeated subjects on *distinct* parent_ids
  could still be misread as convergence.
- **P11 — SKEPTICAL_AUDITOR cannot object to missing loop citations.**
  Auditor is required to cite loop indices it does not possess when the
  target role itself omitted them. The rule structurally produces either
  silence or fabrication.

### Medium

- **P02 — TRAJECTORY_ANALYST has no rule for homogeneous operator history.**
  "Smooth over discontinuities" is the forbidden inference, but the opposite
  (treat monotony as a finding) is unaddressed.
- **P14 — REPORT_SYNTHESIZER may silently drop deterministic findings
  ignored by analysts.** "May use" is permissive, not mandatory.

### Low

- **P08 — n=1 EN event yields an unmarked single-row "table".** Small-n
  guard is global, not EN-row-count-specific.
- **P10 — empty objection space may produce fabricated low-severity nits.**
  Prefix never says "produce zero objections if there are none."

## Required prefix revisions (in priority order)

1. **REPORT_SYNTHESIZER (critical)**: replace the OR with an AND-guarded
   form. Suggested text: *"supported only if deterministic metrics support
   it, OR (at least two analyst roles agree AND at least one cited
   deterministic metric or loop index supports the agreement)."*
2. **TRAJECTORY_ANALYST (high)**: add a "must" — *"must flag any step whose
   metrics are mutually incoherent and refuse to analyse it as a normal
   step."*
3. **ATTRACTOR_DIAGNOSTICIAN (high)**: add an operational discriminator —
   *"branch explosion is indicated by rising open claim count AND repeated
   subjects across distinct parent_ids; treat as a separate diagnosis,
   not as convergence."*
4. **SKEPTICAL_AUDITOR (high)**: add the missing-citation escalation —
   *"if a target role failed to cite loop indices, raise the omission as
   a HIGH-severity objection citing the missing field by name."*
5. **TRAJECTORY_ANALYST (medium)**: add — *"must not narrate stability as
   a finding when the operator field is constant — declare it as missing
   variance."*
6. **REPORT_SYNTHESIZER (medium)**: add — *"include every deterministic
   finding marked high-confidence by `phase_detector` and `diagnostics`,
   even if no analyst mentions it. Cite the deterministic source by
   module name."*
7. **EN_EVENT_ANALYST (low)**: add — *"if there is fewer than one EN event
   per two loops, mark the entire EN analysis as exploratory."*
8. **SKEPTICAL_AUDITOR (low)**: add — *"if no objection meets the
   change-decision test, write 'no objections' under the objections heading
   and proceed to verdict."*

## What this pass does NOT show

- Whether a real DeepSeek model in fact follows the prefix. A prefix can be
  structurally sound and still be ignored. Required next pass: live-LLM
  falsification on each HOLDS probe (paid).
- Whether GLOBAL_CONSTRAINTS actually overrides role-local text under
  conflict. Untested here.
- Multi-trajectory robustness (does P13 echo-chamber bypass replicate across
  domains?). All 13 probes are single-trajectory.

## Replication targets

- Live-LLM P13 (echo-chamber bypass) is the single highest-leverage test.
  If P13 replicates in live LLM behaviour, the synthesizer prefix is unsafe
  as written and must be revised before any further DESi runs are reported.
- Live-LLM P11 (missing-citation paradox) on a probe where TRAJECTORY_ANALYST
  is forced (by ablating its own prefix) to omit loop indices. Tests the
  auditor's failure mode under cascading guardrail breakage.

---

**Status**: EXPLORATORY. 13 probes, single author, no LLM in the loop. Treat
as a *map* of structural risk, not as evidence of behaviour. Do not
incorporate the suggested revisions into `src/desi/roles.py` until a
live-LLM pass replicates at least the critical and high-severity leaks.
