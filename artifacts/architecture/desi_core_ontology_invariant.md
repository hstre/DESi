# DESi Core Ontology Invariant — the immutable epistemic manifold

This document re-anchors the DESi architecture on its **existing** core. It
invents nothing. Every element below already lives in the code; the purpose here
is to make the core visible again and to place the newer (P20–P33) systems
correctly around it.

> **Invariant.** DESi may evolve only at the epistemic *periphery*.
> The epistemic *core space* itself is invariant.
>
> **Peripheral evolution is permitted. Core epistemic-ontology evolution is forbidden.**

## 1. The core is the 9-dimensional state manifold

The DESi core is the closed, fixed-length epistemic state vector defined in
`src/desi/epistemic_trajectory/state.py` (`StateVector`, `DIMENSION_NAMES`). A
DESi *trajectory* is a sequence of these states; trajectory geometry is therefore
well-defined. The nine dimensions are fixed and named verbatim — no invented
axes:

```
frame_id, contradiction_load, anchor_density, source_quality, novelty,
confidence, branch_cost, support_state, routing_state
```

This is the **immutable epistemic manifold**. It is not a claim schema, not a
diff format, not an embedding space. Claims, diffs, embeddings, and benchmarks
*project onto* this manifold; they do not define it.

## 2. Content vs Method partition (5 + 4)

The manifold is partitioned, exhaustively and disjointly, into a content
sub-space and a method sub-space (`src/desi/content_method/features.py`,
`CONTENT_DIMS`, `METHOD_DIMS`; the partition is asserted in code to cover all
nine dimensions and to be disjoint):

| sub-space | dimensions |
| --- | --- |
| **CONTENT (5)** — *what* is being asserted | `frame_id`, `novelty`, `anchor_density`, `contradiction_load`, `source_quality` |
| **METHOD (4)** — *how* the audit moved | `support_state`, `routing_state`, `branch_cost`, `confidence` |

Content and Method must not be mixed. Keeping them separate is what lets DESi
distinguish *a different claim* from *a different way of arriving at the same
claim* — the distinction the periphery (extractor/folding/DBA) keeps
rediscovering by other means.

## 3. T1–T9 are structured epistemic transition operators

`src/desi/models.py` (`Operator`) defines the canonical base scheduler
transitions T1–T9. They are **not** optional heuristics; they are the structured
operators by which a claim moves through epistemic states (the transitions whose
composition *is* a trajectory):

| op | transition | op | transition |
| --- | --- | --- | --- |
| T1 | resolve_conflict | T6 | explore_evidence_path |
| T2 | make_conflict_explicit | T7 | refine_qualifier |
| T3 | request_evidence | T8 | seal_claim |
| T4 | decompose_claim | T9 | trigger_reframing |
| T5 | generate_counter_hypothesis | | |

The paper-8 method operators (recursive_modulation, boundary_condition_analysis,
adaptive_variation_selection, counterexample_search) are *added* alongside T1–T9;
they do not replace them. No further base operators may be invented.

## 4. Trajectory geometry is the dynamics, not the periphery

`src/desi/epistemic_trajectory/metrics.py` (`TrajectoryMetrics`,
`compute_metrics`) computes the geometry of a trajectory over the manifold:

- `smoothness`, `curvature`, `jerk` — first/second/third-order motion of the
  state through the 9-D space;
- `direction_reversal_rate` — how often consecutive steps point in opposing
  directions (negative cosine);
- `frame_flip_rate` — frame_id changes per transition;
- `support_state_instability` — churn in the Method `support_state` dimension;
- `manifold_departure_score` — L2 distance of the final state from the *valid
  manifold centroid* (`compute_centroid`).

Recoverability / blindness is a property of this geometry, already present in the
core and its immediate consumers: `manifold_departure_score` measures how far a
trajectory has left the valid manifold; `DEAD_BRANCH` (`FailureMode`,
`src/desi/models.py`) is the unrecoverable-branch label; State-Vector Blindness
(Failure Mode 11) surfaces structurally unrecoverable pools. The epistemic
conflicts that P31–P33 found "in the predicate / flow direction" are, in core
terms, **direction and curvature in the Method sub-space and frame/ support-state
transitions** — they are already expressible on this manifold.

## 5. What DESi may and may not do

**DESi MAY** (peripheral operations onto the fixed manifold):

- project claims/answers onto the 9-D state space;
- measure trajectory geometry and manifold departure;
- audit, mark, and surface blindness / unrecoverable regions;
- experiment in branch-isolated form;
- compress, route, and trigger escalation.

**DESi MAY NOT** (core-ontology mutation):

- evolve the core ontology or redefine the 9-D structure;
- introduce new epistemic axes;
- mix Content and Method dimensions;
- dynamically re-calibrate epistemic weights of the core dimensions;
- substitute claim heuristics for the state-space itself.

## 6. P20–P33 are periphery that projects onto the core

The following systems are **peripheral**. Each is a projection or a measurement
*onto* the manifold; none defines it, and each may evolve under the periphery
rule above:

| peripheral system (phase) | role | projects onto |
| --- | --- | --- |
| claim extractor (P24/P27/P28/P30) | turn an answer into claim candidates | content dimensions of a state |
| folding / canonicalization (P25/P26) | group claims into regions | reduces redundancy before projection |
| Dual-Builder Adjudication (P15–P19, P29, P31) | compare two independent reconstructions | divergence on the manifold |
| meaning-space alignment (P17/P18) | embedding region similarity | locates claims in the same region |
| typed governance (P19/P32) | symbolic veto on object-level conflicts | contradiction_load / branch_cost |
| region alignment hardening (P32) | remove representation-noise branches | cleaner projection, same manifold |
| epistemic flow layer (P34) | directional relation between claims | Method-space direction / curvature |

These layers are useful and may keep improving. But they are **lenses on the
manifold**, not the manifold.

## 7. P31–P33 as a documented warning

P31–P33 are retained as an explicit cautionary record:

> **Claim-centric governance without a stable epistemic ontology drifts toward
> semantic arbitrariness.**

P31–P33 showed empirically that when adjudication is driven by claim-object
matching, diffing, embeddings, and symbolic vetoes *in isolation from the core*,
the binding conflicts stop sitting in the claim object and start sitting in the
**epistemic transformation / flow direction** — exactly the curvature,
direction-reversal, support-state-instability and manifold-departure quantities
that the core manifold already models. The lesson is not "add more lenses"; it is
"bind the lenses back to the invariant manifold." Object-centric peripheral
governance, grown without that binding, accumulates lens-specific lexicons and
thresholds whose only ground truth is each other — i.e. semantic arbitrariness.

## 8. Scope of this document

This is a re-anchoring, not a redesign. No ontology is added or changed; no new
base axis or operator is introduced; the periphery is left free to evolve. The
core files (`state.py`, `features.py`, `metrics.py`, `models.py`) remain the
single source of truth for the manifold, and this document must be updated to
match them, never the reverse.
