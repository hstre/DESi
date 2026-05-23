# Phase 6 - Public Reviewer Resistance Audit

DESi inspecting its own repo as a skeptical external reviewer would. This is an overreach/attack-surface audit, not self-validation.

**Where would a reviewer attack first?**

The grandiose framing in s1 ('epistemic operating system') and s9.5 ('map of unknown unknowns'); and the all-Class-A domain table (v6-v22) which invites 'too clean to be true' scepticism.

**Which claims read as too strong?**

'hallucination containment at 1.0' (it means visibility, not absence), 'routing cost reduction 53.5%' (mean per-task, not total-workload 7.3%), and 'LangSmith largely unnecessary / counterproductive' (no comparative study).

**Which numbers are not artifact-backed (in this audit)?**

v1-v27 numerics: Table 2 taxonomy results, s3.1 canonical values, s3.3/s9.3 v11.1+v15.3 compression, Table 1 - not traced to artifacts in this round (v28-v38 ARE traced).

**Which terms are philosophically overloaded?**

'epistemic cartography', 'epistemic topology analysis', 'native meta-governance', 'unknown unknowns'. Concrete operations exist beneath them; the language oversells.

**Where is mathematical precision missing?**

Appendix C explicitly omits convergence/compactness/topology proofs; the s9.3 superlinear-savings extrapolation is an unproven engineering implication (labelled as such).

**Which terms trigger hype alarm?**

All 11 forbidden terms appear in the README (s2.2 listing) and trip the rendered-output scanner; the doc must be exempted/whitelisted explicitly.

**Which architecture parts look needlessly complex?**

The Neo4j evolution graph - the system itself flags it as overengineered (efficiency = -0.5). Reported honestly.

**Which parts are genuinely original?**

Replay-bound capture+hash of stochastic LLM output graded by deterministic closed rules; the protected-core / evolvable-periphery boundary with byte-identical core under real mutation (v31/v32); the honest-boundary compression audit (v3.100).

**Which parts resemble known systems in new language?**

Replay = golden-file/differential testing; Concept Gates = multi-condition CI gating; search compression = redundancy pruning with a preservation constraint. The framing is novel; several mechanics are established.

**What would convince a serious systems reviewer?**

The byte-identical replay-drift regression, the determinism scanner at 0, the honest negative results (neo4j overengineered, two sub-ceiling scores, NOT_ENOUGH_INFO handling), and per-claim artifact traceability once the v1-v27 citations are added.
