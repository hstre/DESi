# SPL consolidation analysis — P9

By P8 there were **three** parallel "SPL / projection" layers. This is the
inventory of how they differ, what was duplicated, and the canonical layer that
P9 introduces (`src/desi/spl_core/`) to stop the drift. Empirical validation:
`benchmarks/static_eval/outputs/spl_core_benchmark.md`.

> Framing carried over from P8 and **deliberately preserved**: SPL changes
> *admissibility*, *epistemic projection* and *uncertainty handling* — **not**
> the conflict detection itself. That separation is correct and is not
> "optimised away" here.

---

## 1. The three layers (before P9)

| | **Alexandria SPL** (vendored) | **`desi.spl_adapter`** | **benchmark P8 adapter** |
| - | --- | --- | --- |
| location | `benchmarks/static_eval/vendor/alexandria_spl/` | `src/desi/spl_adapter/` | `benchmarks/static_eval/spl_projection_adapter.py` |
| unit | `SemanticUnit` (text span + offsets) | `SemanticUnit` (canonical_content, raw_span, confidence, ambiguous) | (reuses Alexandria) |
| projection | `SemanticProjection` with full `P_r` | **none** (backend `extract_units → project_units`) | builds Alexandria `SemanticProjection` |
| candidate | `ClaimCandidate(subject, relation, object, relation_score, rank, emission_rule, h_norm)` | `ClaimCandidate(content:str, method, confidence, ambiguous, proposed_relations)` | Alexandria's, as a dict |
| **uncertainty model** | normalised Shannon `h_norm` + Θ thresholds, rules **E0–E4** | **boolean `ambiguous`** + hard **confidence floor 0.5** | Alexandria's |
| gateway | `SPLGateway.submit` (E0–E3) + `emit_claim_nodes` (needs protocol `schema.py`) | `SPLGateway.admit` (closed reason set) → `desi.memory.Claim` | `submit` + a replicated candidate gate |
| output | `ClaimCandidate` → (protocol) `ClaimNode` | `desi.memory.Claim` (state always PROPOSED) | P8 dict |
| network/secrets | none (stdlib) | optional DeepSeek backend (env-only) | none |

### Duplicated / divergent logic

1. **Two ClaimCandidate shapes that cannot be compared.** Alexandria is a
   *structured triple*; `desi.spl_adapter` is a *content string* with no
   subject/predicate/object split and a `proposed_relations` field it is
   forbidden to populate. The benchmark adds a *third* serialisation (a dict).
2. **Two uncertainty models.** Alexandria: continuous `h_norm` over a relation
   distribution, partitioned by τ₂/τ₃ into E1/E2/E3. `desi.spl_adapter`: a binary
   `ambiguous` flag OR `confidence < 0.5`. These answer "is this claim
   admissible?" in completely different currencies.
3. **Two gateways.** Alexandria's `submit` runs emission rules and returns
   candidates; `desi.spl_adapter`'s `admit` runs a closed rejection set
   (`empty_content`, `hallucinated_relation`, `ambiguous_claim`,
   `invalid_method`) and emits real Claims.
4. **`P_r` synthesis lived only in the benchmark adapter** (P8) — so any other
   caller wanting entropy had nowhere canonical to get it.

Left alone, these drift: a fix to entropy in one place silently disagrees with
the others, and "a ClaimCandidate" means three different things.

---

## 2. What becomes canonical, what stays glue

| Component | Verdict |
| --------- | ------- |
| Alexandria entropy model (`h_norm`, Θ, E0–E3) | **canonical** — reimplemented in `spl_core/entropy.py` + `gateway.py` (so `src` doesn't depend on `benchmarks/vendor`), validated against the vendored original (zero drift). |
| Alexandria triple `ClaimCandidate` | **basis of the canonical candidate** — `spl_core/candidate.py` is the triple **plus** a `content` string **plus** an optional `projection_entropy`. |
| `desi.spl_adapter` backends / parser / provenance / cost-guards / `candidate_to_claim` | **kept as production glue** — these touch the outside world (LLM, documents, ledger) and are out of scope for a pure projection core. They feed the canonical candidate via an adapter. |
| `desi.spl_adapter` flag uncertainty (ambiguous + 0.5 floor) | **kept, behind the canonical gateway** as `admit_flag` — a second admissibility *mode*, not a second gateway. |
| Vendored Alexandria SPL | **kept as the external reference oracle** (MIT, unmodified) — used by `spl_core_benchmark.py` to prove the canonical core is faithful. Not imported by `src`. |
| benchmark P8 adapter (`spl_projection_adapter.py`) | **reduced to thin glue** — now delegates to `spl_core`; owns no entropy/gateway logic. |
| Alexandria `emit_claim_nodes` / `ClaimCandidateConverter` | **demo-only for DESi** — needs the protocol-side `schema.py` (not vendored). DESi's converter is `desi.spl_adapter.candidate_to_claim`. |
| Alexandria E4 / `submit_dual` / JSD (dual-builder) | **out of scope** — needs two independent builders; we have one synthetic projection. |

---

## 3. Target architecture

```
raw text / atomic claim (P3)
        │
        ▼
   desi.spl_core  ── the ONE canonical projection / admissibility layer ──
   ┌──────────────────────────────────────────────────────────────────┐
   │ entropy.py   normalized_shannon_entropy, synthesize_relation_dist, │
   │              CanonicalThresholds (Θ)                                │
   │ gateway.py   CanonicalGateway.admit_projection (E0–E3, entropy)     │
   │              CanonicalGateway.admit_flag      (ambiguous+floor)      │
   │ candidate.py CanonicalClaimCandidate (the ONE candidate)            │
   │              from_alexandria_candidate / from_desi_spl_candidate     │
   │ projection.py project_atomic_claim → (candidate, projection)        │
   └──────────────────────────────────────────────────────────────────┘
        │  admissible CanonicalClaimCandidate only
        ▼
   ConflictEngine (P6/P7) ─ predicate typing + entity normalisation ─ UNCHANGED
        ▼
   Governance / ClaimGraph  (epistemic projection — downstream, unchanged)
```

Three adapters land all prior shapes on the one candidate:

- **atomic claim → canonical**: `project_atomic_claim` (entropy model). Used by
  the benchmark adapter and the conflict runner's SPL mode.
- **Alexandria candidate → canonical**: `from_alexandria_candidate` (entropy model).
- **`desi.spl_adapter` candidate → canonical**: `from_desi_spl_candidate` (flag model).

The conflict engine now consumes **only** `CanonicalClaimCandidate`
(`runner` SPL mode builds the comparison dict via `candidate.as_conflict_claim()`).

### The one honest seam left open

There are still **two admissibility modes** behind the one gateway, because the
two source models are genuinely different and `desi.spl_adapter` has **no
distribution** to compute entropy from. Forcing a fake `P_r` onto it would be an
overclaim. Closing the seam = giving the flag model a real `P_r` (its LLM
backend emitting a relation distribution, or a sealed relation matrix), then
routing it through `admit_projection`. Deferred deliberately.

---

## 4. Did P9 help — architecture or benchmark?

From `spl_core_benchmark.md`:

- **Compatibility drift: 0 / 197** projections (dataset claims @ uniform +
  state-derived confidence, plus a confidence sweep). The canonical core
  reproduces the vendored Alexandria gateway exactly — proof the reimplementation
  *reused* the model rather than forking it.
- **Conflict metrics: unchanged.** P9 reproduces P7/P8 exactly (contradiction
  precision/recall 1.00/1.00 at uniform, alias/coref 7/7, multi_valued FP 1/6,
  homonym FP 1/2; SPL-state still blocks 6 rejected claims → recall 0.77).
- **Therefore: architectural gain, not benchmark gain** — exactly as the task
  anticipated, and reported honestly. The win is: one entropy model, one gateway,
  one ClaimCandidate, a clean `src`-owned home, and a drift test that fails loudly
  if anyone forks the behaviour again.

---

## Honesty / limits

- SPL-core is a **projection / admissibility** layer, not the conflict engine,
  not a truth solver, not NER, not an ontology.
- `P_r` is synthesised from a scalar confidence (no NLP backend), so `h_norm` is
  a confidence-shaped quantity, not a measured semantic entropy.
- Two uncertainty models still coexist behind the one gateway; that is documented,
  not hidden, and the path to unifying them is spelled out above.
- The vendored Alexandria stays unmodified (MIT); `src/desi/spl_core` is the
  DESi-owned canonical reimplementation, validated against it.
- No network, no secrets.
