# P10 operational-SPL analysis — making SPL the default pipeline path

P9 made `desi.spl_core` the canonical projection layer (drift 0 vs Alexandria),
introduced `CanonicalClaimCandidate`, and put the conflict *benchmark* runner's
SPL mode behind it. But SPL was **not yet the operational default**: the real
TruthfulQA → ClaimGraph build still wrote raw `(subject, predicate, object)`
triples straight into memory. P10 closes that.

This is the bypass inventory (before P10), what P10 changed, and what is
deliberately left un-projected.

---

## 1. Pipeline paths and their SPL status (before P10)

| stage | file | what it produces | SPL status (pre-P10) |
| ----- | ---- | ---------------- | -------------------- |
| P0 | `claim_memory_adapter.py` | answer-level Claim (whole free-text answer) + gold ref | **not projected** — see §3 (by design: provenance anchor, not an atomic comparable claim) |
| P1 | `trajectory_builder.py` + `MemoryHook` | governance trajectory claims via `run_desi` | **n/a** — these are run/step records, not atomic S/P/O claims |
| P2 | `freetext_claim_extractor.py` | rule-based sub-claims (subject + text) | feeds P3 as fallback; not projected on its own |
| P3 | `model_claim_extractor.py` | **atomic `(subject, predicate, object, confidence, claim_type)`** | **BYPASS** — the claim graph recorded these raw |
| P3→graph | `claim_graph_pipeline.py` step 3 | atomic Claims + DERIVES_FROM / gold edges | **BYPASS** — `rec.record_claim(content="s | p | o", …)` with no projection |
| P4–P7 | `cross_claim_contradictions.py`, `conflict_benchmark_runner.py` | conflict detection | default `spl_mode=None` compares **raw triples**; SPL mode (P9) uses canonical candidates |
| P8 | `spl_projection_adapter.py` | P8 dict | clean (P9: delegates to `spl_core`) |
| P9 | `src/desi/spl_core/` | canonical candidate / gateway | the canonical layer itself |

**The load-bearing bypass:** `claim_graph_pipeline.py` step 3. The atomic P3
claims — the ones that are *meant* to become comparable nodes and feed the
conflict engine — went `extract → record_claim` directly. That is exactly the
`atomic claim → ClaimGraph` shortcut the target architecture forbids.

A secondary bypass: `conflict_benchmark_runner.py` with `spl_mode=None` compares
raw triples. This is **kept on purpose** as the P6/P7 symbolic baseline and as a
debug/comparison mode — it is no longer the "standard" mode (the SPL modes are),
but it must remain so the benchmark can show SPL changes nothing in detection.

---

## 2. What P10 changed (operational default)

`claim_graph_pipeline.py`:

```
P3 atomic claim
  → spl_core.project_atomic_claim(claim)      ← NEW, default (use_spl=True)
  → CanonicalClaimCandidate (+ CanonicalProjection)
  → record_claim(... operator_path=(task, "p3", "spl:<rule>", "h=<entropy>", "<admissibility>"))
  → DERIVES_FROM answer  (always — lineage)
  → SUPPORTS/CONTRADICTS gold  (only if admissible — comparable)
```

Concretely:

1. **Every** P3 claim is projected before it may enter the graph. `use_spl=True`
   is the default; `--allow-raw-claims` is the debug/legacy bypass.
2. **Projection metadata is stored in the ClaimGraph** — both in the stored
   Claim's `provenance.operator_path` (so memory itself carries the projection
   trail: emission rule, `h_norm`, admissibility) and in the exported atomic row
   (`projection_method`, `projection_entropy`, `emission_rule`, `admissible`,
   `gateway_state`, `source_projection`, `flags`).
3. **Only admissible candidates get comparable (gold SUPPORTS/CONTRADICTS)
   edges.** Inadmissible claims are still recorded (auditable, never silently
   dropped) but quarantined: they carry governance flags and do not get
   conflict-eligible relations.
4. **Governance flags** (`src/desi/spl_core/governance.py`,
   `projection_flags`): `projection_uncertain` (admitted E2), `projection_invalid`
   (gate rejected), `projection_high_entropy` (E3 ambiguity block).
5. **The conflict engine sees only canonical candidates** in standard mode
   (already true for the runner since P9; the claim graph now produces canonical
   candidates too).

Result (from `outputs/p10_operational_spl_benchmark.md`, over the real DeepSeek
limit-50 graph): **bypass count 48 → 0**; projection rejection rate 6.2% (the
low-confidence extractions); conflict precision/recall unchanged.

---

## 3. What is still NOT projected — and why (honest boundaries)

- **Answer-level claims (P0).** The whole free-text answer is recorded as one
  Claim that the atomic claims `DERIVES_FROM`. It is a **provenance anchor**, not
  an atomic comparable assertion, so `project_atomic_claim` (which expects an
  S/P/O triple) does not apply. The *production* path for turning free text into
  claims is `desi.spl_adapter` (backend `extract_units → project_units →
  admit`), which is itself an SPL gateway; wiring the benchmark's answer text
  through it is future work, not a silent raw path. The atomic claims that
  actually feed conflict detection **are** projected.
- **Gold reference claims.** These are ground-truth anchors (`state=CONFIRMED`,
  confidence 1.0), not model output; they are reference nodes, not candidates.
- **`run_desi` trajectory / governance claims (P1).** Run/step records, not
  atomic assertions.
- **The raw P6/P7 conflict mode** (`spl_mode=None`) and `--allow-raw-claims`.
  Explicitly **debug/legacy**, retained for the P9/P10 comparison that proves SPL
  does not change detection.

So: no atomic comparable claim reaches the graph or the conflict engine
un-projected in standard mode. The remaining un-projected nodes are
provenance/reference anchors or explicit debug modes — documented, not hidden.

---

## 4. Did P10 help — architecture/governance or benchmark?

**Architecture + governance, honestly.** From the benchmark:

- **Bypass count 48 → 0** — the structural win: atomic claims are now admitted
  through SPL, with projection metadata in memory and the graph.
- **Projection rejection rate 6.2%** on real confidences (the two 0.5-confidence
  DeepSeek extractions + one structurally incomplete triple), flagged
  `projection_invalid` / `projection_high_entropy`. A real, graded gate — not the
  offline 0.5-fallback artifact (which blocks everything and is reported as such).
- **Governance now keys off projection, not raw strings**: every atomic claim
  carries an emission rule, an entropy, an admissibility verdict, and flags.
- **Conflict precision/recall unchanged (1.00/1.00)** — SPL changes admissibility
  and provenance, not detection. The cross-tab confirms SPL is truth-agnostic
  (not a hallucination filter).

No artificial improvement was introduced. SPL is, as before, a
projection/admissibility layer — not a truth solver, not NER, not an ontology.
