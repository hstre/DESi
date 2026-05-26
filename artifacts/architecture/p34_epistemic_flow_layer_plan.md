# P34 — Epistemic Flow Layer (architecture plan)

## Why object-centric governance is not enough

DESi's adjudication, through P32, compares two independent reconstructions of an
answer by their **claim objects**: same subject + same predicate-core + same
object content → same region; an object-level negation / antonym / rival value →
a typed veto that holds the branch open. P32 made this precise and robust to
*representation noise* (placeholder Yes/No objects, negation-token variants,
tense, granularity), cutting the P31 escalation branches 8→1.

But the comparison is still **positional and lexical**: the disputed content has
to live in the OBJECT slot for a veto to fire. The epistemic relationship between
two claims — does the second *strengthen, weaken, negate, reverse, hedge,
condition or exclude* the first — is never modelled directly. It is only inferred
from object-token overlap and a fixed lexicon of object words.

## How P33 made the limit visible

P33 stress-tested the symbolic layer with 37 deliberately hard, paraphrased
conflicts. 25/37 held; **12 were falsely reconciled**. Every miss shared one
property: *both sides read the same polarity on the OBJECT*, because the conflict
lived in the **predicate verb**, a **softener**, or a **determiner**:

- predicate-position antonyms, even in-lexicon: `increases risk` vs `decreases
  risk` (A4);
- out-of-lexicon verb antonyms: `supports` vs `refutes` (AO2), `promotes` vs
  `prevents` (P3), `helps` vs `damages` (AO3);
- paraphrased negation with no negation token: `fails to produce injury`,
  `is free of toxicity`, `lacks conductivity` (P1/P2/P4);
- frequency softeners: `rarely` / `unlikely` / `seldom` dangerous (F1/F2/F3);
- `always occurs` vs `never occurs` (Q4);
- a determiner-polluted causal role swap (`the virus causes the symptoms` vs
  `the symptoms cause the virus`, C4).

The objects were identical (`risk`, `claim`, `recovery`, `injury`, …) so the
object-centric layer saw agreement. The embedding layer shared the gap (it failed
to co-locate `not cause harm` and `harmless`), so "more embedding" is not the fix.
The binding limit is the **direction** of the assertion, which is carried by the
predicate, not the object.

## Three different things — and why they are not interchangeable

1. **Semantic similarity** (P18 meaning-space, embeddings): "are these two claims
   about the same region?" It locates claims; it cannot tell apart "X causes Y"
   from "X prevents Y" (same region, opposite direction) — by design it smooths
   over exactly the polarity we must keep.
2. **Typed divergence** (P19/P32): "is there a typed logical conflict on the
   shared region?" Robust, symbolic, but OBJECT-CENTRIC and lexicon-bound — it
   fires on object negation / antonym / rival value, and misses predicate-carried
   direction.
3. **Epistemic flow** (P34): "what is the directional RELATION from claim A to
   claim B?" — `same / strengthened / weakened / negated / reversed / hedged /
   conditioned / excluded / orthogonal / unresolved`. It reads the PREDICATE as a
   direction operator (polarity of direction-verbs, frequency level, modality
   level, causal role order) over a region established by subject + non-subject
   content.

Similarity answers *where*; typed divergence answers *is there a known conflict
shape on the object*; flow answers *which way does B move relative to A*. Flow is
the missing axis: it turns governance from object comparison into epistemic
dynamics.

## Why this is more Alexandria-conformant

Alexandria's principle is **dual-builder adjudication that preserves genuine
divergence** — "semantics may reconcile, logic may veto" — without a judge, a
truth score, or a majority vote. The object-centric veto is a partial realisation
of that principle: it preserves divergence only when the divergence happens to
sit in the object. Modelling epistemic *flow* preserves divergence wherever it
sits — a reversal, a weakening, a paraphrased negation — which is what "do not
silently reconcile two genuinely different reconstructions" actually requires.
Crucially, flow stays inside the Alexandria constraints: it characterises the
**relation between two reconstructions** (B negates / weakens / reverses A), never
which one is true. It is a governance/direction signal, not a verdict.

## Design (prototype)

- Decompose each claim into a **flow signature**: a region core (subject +
  non-marker content, lightly stemmed), a **polarity** (lexical-negation sign ×
  direction-verb sign — the two kinds of negation are independent, never
  double-counted), a **frequency** level, a **modality** level, a condition flag,
  and the raw subject/object for causal-reversal detection. Direction verbs,
  negation, frequency and modality are *flow markers*, removed from the region
  content.
- `epistemic_flow(A, B)`: causal role swap → `reversed_flow`; else if region
  cores don't overlap → `orthogonal_flow` (defer to the object layer); a flip is
  only judged when the **non-subject content** overlaps (sharing only the subject
  defers, so "road is safe" vs "road is not dangerous" is not a false negate);
  opposite polarity → `negated_flow`; same polarity with a condition / frequency
  drop / modality drop → `conditioned / weakened / hedged`; else `same_flow`.
- Governance rule: `negated`/`reversed` → `logical_polarity_conflict` (hard);
  `weakened`/`hedged`/`conditioned`/`excluded` → `protected_branch_required`
  (soft); `same` → close allowed; `orthogonal`/`unresolved` → defer to the P32
  object layer. Flow **augments** P32 (object-slot vetoes keep working), it does
  not replace it.

## Honesty constraints

Heuristic, English-specific, lexicon-based; a governance/direction layer, not a
truth system and not a semantic engine. It says *how* two reconstructions relate,
never which is correct. Validated offline on the P33 adversarial set; no API
calls, no solver, no judge, no vote.
