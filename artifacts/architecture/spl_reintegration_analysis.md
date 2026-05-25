# SPL (Alexandria) reintegration analysis — P8

Goal: integrate the **Alexandria Semantic Projection Layer (SPL)** as a real
semantic *intermediate* layer in the DESi benchmark pipeline, so the path is

```
atomic claim (P3) → SemanticUnit → SemanticProjection → ClaimCandidate
                  → SPLGateway → (DESi) Claim / conflict engine
```

and **never** raw S/P/O → ClaimNode directly.

This is the inventory + design rationale. The implementation it describes is
`benchmarks/static_eval/spl_projection_adapter.py` (the adapter) and the
`--use-spl-projection` mode of `conflict_benchmark_runner.py`. The empirical
result lives in `outputs/spl_vs_symbolic_benchmark.md`.

---

## 0. Three things called "SPL" — disambiguation (read this first)

There are **three** distinct artefacts with "SPL" in the name. Conflating them
is the single biggest risk to understanding this work, so they are named
explicitly everywhere:

| # | Name | Location | What it is |
| - | ---- | -------- | ---------- |
| 1 | **External Alexandria SPL** (WP2) | `benchmarks/static_eval/vendor/alexandria_spl/` (`spl.py`, `spl_gateway.py`) | The *probabilistic* projection layer from the public repo. Adds `P_r` distributions, normalised Shannon entropy `h_norm`, emission rules E0–E4, and `SPLGateway.submit/emit_claim_nodes`. **Vendored unmodified** (MIT, © Steffen Rentschler). |
| 2 | **In-repo `desi.spl_adapter`** | `src/desi/spl_adapter/` | A DESi-native, *production-oriented* SPL-style adapter that already exists: its own `SemanticUnit`, `ClaimCandidate`, `SPLGateway.admit(...)`, `candidate_to_claim(...) → desi.memory Claim`, deterministic + DeepSeek backends, source parsing, provenance, cost guards. **It is read-only w.r.t. memory.** Crucially it has **no** WP2 probabilistic projection — no `P_r`, no `h_norm`, no E0–E4 entropy gate. Its "projection" is `backend.extract_units → project_units → candidates`. |
| 3 | **New DESi benchmark adapter** | `benchmarks/static_eval/spl_projection_adapter.py` | The glue written in P8. Drives artefact #1 from a P3 atomic-claim dict. **DESi code, not original SPL.** |

The important structural observation: **#2 already gives DESi the
candidate→Claim boundary; what #2 lacks is exactly the probabilistic entropy
gate that #1 provides.** So the external SPL is not a competitor to the in-repo
adapter — it is the missing *upstream* (ambiguity-aware) projection stage. See
§6 for what a non-benchmark reintegration would look like.

---

## 1. Was the SPL really importable? Which APIs are stable vs demo-only?

**Yes — fully importable, offline, stdlib-only.** Cloned from
`github.com/hstre/Alexandria-Semantic-Projection-Layer`, MIT-licensed.
`spl.py` and `spl_gateway.py` import only `math`, `time`, `uuid`, `hashlib`,
`json`, `os`, `re`, `dataclasses`, `enum`, `typing`. No NLP backend, no network,
no third-party deps. They are vendored unmodified (see `vendor/.../VENDOR.md`).
`spl_gateway.py` does `from spl import …`, so the vendor dir is placed on
`sys.path` as a flat module location, not imported as a package.

**Stable / usable (the probabilistic layer — what the adapter uses):**

| Component | Status | Notes |
| --------- | ------ | ----- |
| `SemanticUnit` / `.new()` / `.to_dict()` | **stable** | Plain dataclass, pure constructor. |
| `SemanticProjection` (fields `P_r`, `subject_candidates`, `object_candidates`, `P_modality`, `P_category`, `h_norm`, `status`, `emission_rule`, `p_illegal`) | **stable** | The data object; `P_r` must be supplied (no builder here). |
| `compute_h_norm`, `compute_jsd` | **stable** | Pure functions, WP2 §7.1 / §3.3.5. |
| `EmissionEngine.emit(projection, k)` (E0–E3) | **stable** | Deterministic given `P_r` + thresholds. |
| `SPLGateway.submit(projection, k)` → `SPLResult` | **stable** | `is_ready()`, `is_blocked()`, `top_candidate()`, `h_norm`, `candidates`. **This is the layer the adapter drives.** |
| `SPLThresholds` Θ = {τ₀..τ₄} + `validate()` | **stable** | WP2 recommended defaults. |
| `ClaimCandidate` (`subject`, `relation`, `object`, `relation_score`, `rank`, `emission_rule`, `h_norm`) | **stable** | The pre-protocol triple. |
| `GatewayEvent`, audit log, `summary()` | **stable** | Side-effect: writes `audit_log.json` unless `audit_log_path=None` (we pass `None`). |

**Demo-only / not usable here (the protocol boundary):**

| Component | Why not usable in the benchmark |
| --------- | ------------------------------- |
| `SPLGateway.emit_claim_nodes()` / `to_claims()` | These route through `ClaimCandidateConverter.convert()`, which does `from .schema import ClaimNode, BuilderOrigin, Category, Modality`. That **protocol-side `schema.py` is deliberately not vendored** — it belongs to the Alexandria *protocol*, and DESi already has its own `desi.memory` Claim/ClaimNode layer. So in DESi this path is dead: the SPL's "only legal path to a ClaimNode" terminates at a *validated `ClaimCandidate`*, and the **DESi memory layer is the converter on the other side of that boundary** (in production, that converter is `desi.spl_adapter.candidate_to_claim`). |
| `ClaimCandidateConverter`, `_CATEGORY_HINT_MAP`, `_MODALITY_HINT_MAP` | Same reason — need protocol `schema.py`. |
| Dual-builder `submit_dual` / E4 / `apply_e4` | Requires two independent builders (alpha/beta) projecting the same unit. We have one synthetic projection per claim, so E4 (builder divergence) is out of scope; documented, not used. |
| `matrix_seal_hash`, `matrix_version` governance | Real values need a sealed relation matrix `M` (WP2 Appendix K). We stamp a synthetic `matrix_version="desi-spl-adapter-v1-synthetic-Pr"` so audit trails never mistake the synthetic `P_r` for a real matrix. |

**Critical honesty point about `P_r`.** The real SPL derives `P_r` from an NLP
relation matrix (WP2 §3.3) — *that builder is explicitly not in the module*
(its own docstring says so: "It does NOT implement the full SPL computation —
that requires an NLP backend"). We have no such backend. The adapter therefore
**synthesises** `P_r` from the extractor's scalar confidence (see §3). So `h_norm`
here is a *confidence-shaped* quantity, **not** a measured semantic entropy. The
emission machinery (E0–E4, thresholds, gateway) is genuine, unmodified SPL; the
distribution it consumes is a DESi heuristic.

---

## 2. Does the adapter work?

Yes. `benchmarks/static_eval/spl_projection_adapter.py` exposes

```python
project_atomic_claim_to_candidate(claim: dict) -> dict
# -> {semantic_unit, semantic_projection, claim_candidate,
#     projection_entropy, projection_method:"spl_adapter",
#     gateway_valid, errors, emission_status, emission_rule}
```

Smoke output (calibration working as designed, `relation_space_size=8`):

```
conf=0.90 'Abraham Lincoln|birth year|1809' -> E1  h_norm=0.250 gateway_valid=True
conf=0.70 'the Earth|is|flat'                -> E2  h_norm=0.574 gateway_valid=True
conf=0.45 'the suspect|was in|London'        -> E3  h_norm=0.846 gateway_valid=False (blocked)
conf=0.70 '||'  (empty)                       -> E2  h_norm=0.574 gateway_valid=False (structural)
```

`gateway_valid` faithfully replicates the gateway's *candidate-validation gate*
(`SPLGateway._validate_candidate`: emission rule ∈ {E1,E2}, confidence ≥ τ₁ for
E1, `h_norm` < τ₂/τ₃, evidence ≥ 1) **plus** the structural check that
`emit_claim_nodes` would apply (non-empty subject/relation/object). It stops
before the protocol-`schema.py` conversion (§1).

---

## 3. How does SPL prevent "raw text → ClaimNode" directly?

The SPL invariant (WP2 §2, repeated in `spl.py`'s docstring):

> No text fragment may become a canonical ClaimNode directly. The path is:
> text → SemanticUnit → SemanticProjection → ClaimCandidate →
> (ClaimCandidateConverter) → ClaimNode.

The adapter enforces this for the DESi benchmark by construction:

1. **A claim must become a `SemanticUnit`** (`SemanticUnit.new(source_text=…)`).
   A raw `{subject, predicate, object}` dict is not a unit until wrapped.
2. **It must be projected** into a `SemanticProjection` carrying a full `P_r`
   distribution (the adapter synthesises one; a real backend would compute it).
3. **It must survive the emission rules.** `SPLGateway.submit` runs E0–E3:
   - **E0** (structural shield): `p_illegal > τ₀` → `STRUCTURAL_VIOLATION`, no candidate.
   - **E3** (ambiguity block): `h_norm ≥ τ₃` (0.65) → `AMBIGUOUS`, no candidate.
   - **E1/E2** (singular / top-k): only here is a `ClaimCandidate` emitted.
   A blocked projection yields **zero** candidates — there is nothing to compare
   or convert.
4. **Only a validated `ClaimCandidate` crosses the boundary.** In the benchmark
   the conflict engine receives candidates, never raw triples (§5). In
   production, `desi.spl_adapter.candidate_to_claim` is the converter that turns a
   candidate into a `desi.memory.Claim`. Either way, the raw triple is *not* the
   admissible unit.

So "raw → claim" is structurally impossible in `--use-spl-projection` mode: a
claim that fails projection (E0/E3) or is structurally empty is simply never
emitted as a candidate, and the downstream stages only ever see candidates.

---

## 4. Where does SPL sit between P3 extraction and the P6/P7 conflict engine?

```
P3 model_claim_extractor  →  atomic claim dict {s,p,o,confidence}
        │
        ▼   benchmarks/static_eval/spl_projection_adapter.py   ← NEW (P8)
   SemanticUnit ─► SemanticProjection (synth P_r, h_norm) ─► SPLGateway.submit
        │                                   │
        │                              E0/E3 block ──► claim dropped (not comparable)
        ▼  E1/E2
   ClaimCandidate (validated, carries h_norm + emission rule + provenance)
        │
        ▼   conflict_benchmark_runner.py  (--use-spl-projection)
   P6/P7 conflict engine  (predicate typing + entity normalisation, UNCHANGED)
        │
        ▼
   Conflict / governance signal
```

SPL is the **admissibility / projection** stage: it decides *which atomic claims
are well-formed and confident enough to become comparable candidates*. The P6/P7
conflict engine is the **relational** stage: given comparable candidates, it
decides *which pairs conflict*. They are deliberately separate jobs (§5).

---

## 5. Does SPL improve P7, or just make it architecturally cleaner? Is direct raw comparison now avoidable?

Empirically (`outputs/spl_vs_symbolic_benchmark.md`, 46 pairs):

| metric | P7 symbolic | SPL (uniform 0.70) | SPL (state-derived conf) |
| ------ | ----------- | ------------------ | ------------------------ |
| exact-match | 42/46 | **42/46 (identical)** | 36/46 |
| contradiction recall | 1.00 | **1.00 (identical)** | 0.77 |
| contradiction precision | 1.00 | 1.00 | 1.00 |
| alias/coref recall | 7/7 | **7/7 (identical)** | 5/7 |
| multi_valued FP | 1/6 | 1/6 | 1/6 |
| homonym/merge FP | 1/2 | 1/2 | 1/2 |
| gateway-invalid claims | — | 0 | 6 |
| pairs suppressed | — | 0 | 6 |

**It makes things architecturally cleaner; it does not improve the metrics.**

- **No metric gain.** At the benchmark's uniform 0.70 confidence, every claim
  emits as E2 and passes the gate, so the conflict engine sees the *identical*
  candidates → identical numbers. SPL does **not** rewrite subjects/objects, so
  it cannot by itself catch an alias or a coreference; that remains the
  entity-normalisation stage's job, running unchanged.
- **The gate is real (state mode).** When confidence carries epistemic meaning,
  the gate fires: rejected claims (conf 0.40) cross τ₃, are E3-blocked, and their
  pairs are suppressed — which *lowers* contradiction recall (1.00 → 0.77). This
  is an honest, instructive **negative** result: the entropy gate is a
  *pre-filter on claim admissibility*, and coupling it naively to claim-state
  removes the very low-standing claims a contradiction check wants to see. "What
  may become a claim" and "which claims conflict" are different jobs; the gate
  does the first, not the second.
- **Direct raw comparison is now structurally avoidable — yes.** With
  `--use-spl-projection` the conflict engine only ever receives candidates
  emitted by `SPLGateway.submit()`; a claim that fails projection is never
  compared. The benchmark confirms this changes *admissibility*, not *detection
  quality*.

---

## 6. Recommendation for a non-benchmark reintegration (beyond P8)

The benchmark adapter (#3) intentionally synthesises `P_r`. The clean,
non-synthetic path forward is to **unify the two in-repo layers** rather than
keep three SPLs:

1. Give `desi.spl_adapter`'s backend a real `P_r`/`h_norm` (its LLM backend can
   emit a relation distribution, or a small relation matrix can be sealed),
   then run the **external SPL's `EmissionEngine`** (E0–E3) on it.
2. Feed the external SPL's emission decision + `h_norm` into
   `desi.spl_adapter.SPLGateway.admit`, so the existing `candidate_to_claim →
   desi.memory.Claim` boundary gains the WP2 ambiguity gate it currently lacks.
3. Keep the conflict engine (P6/P7) downstream and unchanged — it already
   operates on candidates.

That would make the entropy gate operate on *measured* uncertainty instead of a
confidence proxy, which is the only way SPL could plausibly improve detection
rather than just admissibility.

---

## Honesty / limits (summary)

- The external SPL is genuine, unmodified, importable, stdlib-only — but its
  `P_r` **builder is not included** (by its own design). We synthesise `P_r`; the
  emission math is real, the distribution is a heuristic.
- SPL is a **projection / validation layer**, not a truth solver, not NER, not an
  ontology. It gates admissibility; it does not adjudicate truth or merge
  entities.
- On this dataset SPL does not improve conflict metrics; its value is the
  enforced invariant (no raw → claim), the auditable per-candidate provenance
  (`h_norm` + emission rule), and a *functioning* ambiguity gate — demonstrated,
  with its recall cost honestly reported, in the state-mode column.
- No network, no secrets; `audit_log_path=None` so the gateway writes no files.
