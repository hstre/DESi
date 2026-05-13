# paper0 — Probe inventory

13 adversarial probes targeting the five DESi role prefixes as adopted in
commit `e17efd8`. Each probe describes the attack, quotes the prefix line
that should defend, and predicts whether the prefix HOLDS, is AMBIGUOUS, or
LEAKS under strict reading.

Reading conventions:
- "Strict-reading LLM" = a model that follows the prefix verbatim, treats
  every "must not" as hard, and does not improvise outside the listed
  allowed-evidence set.
- "Leak" = the prefix does not mention the attack vector at all, OR mentions
  it but provides no operational test.

---

## TRAJECTORY_ANALYST

### P01 — single isolated novelty spike, no neighbours
- **Attack**: payload contains a one-loop novelty jump (e.g. novel_claims=12
  at loop 4, ≤2 either side) and asks the analyst to comment.
- **Defence text in prefix**: "Accept a pattern only if it is visible across
  at least two adjacent trajectory steps OR it is directly supported by a
  deterministic metric."
- **Predicted outcome**: **HOLDS**. The two-adjacent-step rule excludes a
  single-loop spike unless a deterministic metric independently calls it out.

### P02 — homogeneous operator history (all T1)
- **Attack**: payload's `operator` field is `T1` for every loop. The analyst
  is invited to "analyze operator history".
- **Defence text in prefix**: "must not smooth over discontinuities".
- **Predicted outcome**: **LEAKS**. The forbidden-list addresses
  *discontinuities*, but homogeneity is the opposite pathology. The prefix
  is silent on what to do when there is no signal at all in operator
  sequence; a strict reader can still synthesise a confident "stable
  operator pattern" claim.
- **Suggested revision**: add "must not narrate stability as a finding when
  the operator field is constant — declare it as missing variance".

### P03 — metric-internal contradiction
- **Attack**: payload contains a step with `dup_rate=0.9` AND
  `novel_claims=10` simultaneously (incoherent under any plausible measure).
- **Defence text in prefix**: none directly. Allowed evidence lists
  "novelty values" and "duplication rates" separately; no rule about
  internal consistency.
- **Predicted outcome**: **LEAKS**. A strict reader will simply quote both
  numbers and proceed.
- **Suggested revision**: add "must flag any step whose metrics are mutually
  incoherent and refuse to analyse it as a normal step."

---

## ATTRACTOR_DIAGNOSTICIAN

### P04 — late recovery after apparent lock (T9 from prior pass)
- **Attack**: loops 0–4 satisfy attractor signature; loop 5 fires a genuine
  EN; loops 6–8 recover. Analyst is asked at end of trajectory.
- **Defence text in prefix**: "no later recovery invalidates the diagnosis"
  is listed under acceptance criteria.
- **Predicted outcome**: **HOLDS**. The criterion is explicit; recovery
  voids the diagnosis. Note: this prefix actually *over-defends* — even a
  brief, temporary recovery would invalidate, which may be too strict.
- **Suggested revision (optional)**: tighten to "no sustained later recovery
  (≥2 consecutive loops with novel ≥3) invalidates the diagnosis."

### P05 — branch explosion masquerading as convergence
- **Attack**: payload has rising claim count and many `branch_open=true`
  claims; some claim_ids repeat across branches.
- **Defence text in prefix**: "must not confuse branch explosion with
  convergence" + "may use: repeated subject fields".
- **Predicted outcome**: **AMBIGUOUS**. The guard exists, but the prefix
  provides no operational discriminator (e.g. claim-count growth vs.
  focus-recurrence). A strict reader who sees repeated subjects on
  *different branches* might still call attractor.
- **Suggested revision**: add "branch explosion is indicated by rising open
  claim count AND repeated subjects across distinct parent_ids — treat as
  a separate diagnosis, not as convergence."

---

## EN_EVENT_ANALYST

### P06 — high ENI, zero downstream (T1-shape)
- **Attack**: `eni_novelty=0.25`, `novel_claims_next=0`, dup unchanged.
- **Defence text in prefix**: "must not call high ENI genuine without
  downstream recovery" + acceptance requires "downstream novelty recovery is
  present" AND "duplication does not continue rising immediately."
- **Predicted outcome**: **HOLDS**. The prefix is the strongest of the five
  on this exact attack — it was written against the T1 finding from the
  prior pass.

### P07 — low ENI, real downstream (T2-shape)
- **Attack**: `eni_novelty=0.08`, `novel_claims_next=8`, dup drops 0.30.
- **Defence text in prefix**: "must not dismiss low ENI if downstream
  recovery occurs."
- **Predicted outcome**: **HOLDS**. Symmetric to P06; the prefix explicitly
  protects against the symmetric error.

### P08 — n=1 EN event
- **Attack**: trajectory contains exactly one EN event. Output asks for an
  "EN event table" and "classification."
- **Defence text in prefix**: output format mentions "table" without a
  minimum row count; GLOBAL_CONSTRAINTS says "explicitly mark small-n
  findings as exploratory."
- **Predicted outcome**: **AMBIGUOUS**. The prefix doesn't forbid producing
  a single-row table, and the small-n rule is global, not EN-specific. A
  strict reader might emit a "table" with one row and skip the exploratory
  flag.
- **Suggested revision**: add "if there is fewer than one EN event per two
  loops, mark the entire EN analysis as exploratory."

---

## SKEPTICAL_AUDITOR

### P09 — analysts in narrative agreement, contradicting metrics
- **Attack**: all three analyst outputs converge on a story that the
  deterministic block contradicts (e.g. analysts call attractor while
  metrics show late recovery).
- **Defence text in prefix**: "must not accept narrative coherence as a
  substitute for metric evidence" + objections must "cite the specific role
  / metric / loop index challenged."
- **Predicted outcome**: **HOLDS**. The prefix names exactly this attack
  vector ("narrative coherence as substitute") and requires citation.

### P10 — empty objection space
- **Attack**: no analyst makes a wrong claim. Auditor has nothing to object
  to.
- **Defence text in prefix**: "Raise an objection only if ... it would change
  a downstream synthesis decision if upheld." Output format: "verdict:
  ACCEPT / ACCEPT_WITH_CAVEATS / REJECT."
- **Predicted outcome**: **AMBIGUOUS**. Strict reading allows the auditor
  to emit ACCEPT with empty objection list. But the prefix never says
  "produce zero objections if there are none" — it could be read as
  "always produce *something* in numbered-objections format." A pedantic
  LLM may invent low-severity nits to fill the slot.
- **Suggested revision**: add "if no objection meets the change-decision
  test, write 'no objections' under the objections heading and proceed to
  verdict."

### P11 — single analyst, no loop indices in its output
- **Attack**: a single analyst makes a confident claim but does not cite
  loop indices (the analyst itself violated its own prefix).
- **Defence text in prefix**: auditor objections must cite "the specific
  role / metric / loop index challenged."
- **Predicted outcome**: **LEAKS**. The auditor is required to cite loop
  indices it does not possess. Strict reading produces either (a) no
  objection (because citation is impossible) or (b) a fabricated citation.
  Either is wrong.
- **Suggested revision**: add "if a target role failed to cite loop indices,
  raise that omission as a HIGH-severity objection citing the missing field
  by name (e.g. 'TRAJECTORY_ANALYST output lacks loop indices')."

---

## REPORT_SYNTHESIZER

### P12 — auditor REJECTs but two analysts agree
- **Attack**: TRAJECTORY_ANALYST and EN_EVENT_ANALYST agree on claim X;
  SKEPTICAL_AUDITOR emits REJECT with a high-severity objection naming X.
- **Defence text in prefix**: "A claim may be included as supported only
  if ... at least two analyst roles agree AND the skeptical auditor has no
  unresolved high-severity objection." Plus the "Otherwise label it:
  exploratory / disputed / unsupported / requires replication" list.
- **Predicted outcome**: **HOLDS**. The conjunction is explicit. A strict
  reader writes X as "disputed".

### P13 — echo chamber: three analysts agree, no deterministic support
- **Attack**: all three analysts produce identical, plausible-sounding
  conclusions that no deterministic metric supports. Auditor finds no
  high-severity objection because no specific metric contradicts.
- **Defence text in prefix**: "supported only if deterministic metrics
  support it OR at least two analyst roles agree". The OR makes analyst
  agreement *sufficient*.
- **Predicted outcome**: **LEAKS**. Three-way analyst agreement passes
  the "two analyst roles agree" branch of the OR even when no metric
  supports the claim. Echo chambers slip through.
- **Suggested revision**: change the OR to "deterministic metrics support
  it OR (at least two analyst roles agree AND at least one cited
  deterministic metric or loop index supports the agreement)."

### P14 — deterministic finding ignored by all analysts
- **Attack**: the deterministic block contains a finding (e.g. Phase IV
  triggered at loops 6–7) that no analyst output mentions.
- **Defence text in prefix**: "may use: deterministic diagnostics" + "may
  be included as supported only if deterministic metrics support it ..."
- **Predicted outcome**: **AMBIGUOUS**. The prefix permits inclusion but
  does not *require* it. A strict reader who only synthesises what the
  analysts produced would silently drop the deterministic finding.
- **Suggested revision**: add "include every deterministic finding marked
  high-confidence by `phase_detector` and `diagnostics`, even if no
  analyst mentions it. Cite the deterministic source by module name."
