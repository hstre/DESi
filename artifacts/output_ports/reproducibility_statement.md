# Reproducibility Statement - A Read-Only Governance Layer for In-Context Exploration: A Small Synthetic Follow-Up Study

## Reproducibility Statement

Every metric is computed by deterministic arithmetic over fixed synthetic fixtures (no PRNG, no learned model). All 8 reported numbers are derived from a named sprint and recomputed bit-identically, with a deterministic hash chain recorded across phases (claim traceability 1.0). The study is replay-exact and scoped to the sandbox.

## Replay Hashes

Every metric is recomputed bit-identically and a deterministic hash chain is recorded across phases. Per-sprint replay hashes (14):

- 1ff033aacae3a30c
- 3f6014fcf46e036a
- 4537fff62dc471b6
- 6aab7777d70929ae
- 7059a47ff1293e72
- 92150159bd2ba7ba
- a1cdf557f2824a4b
- a3d9d5922d8ffbf1
- a969b4243ff24691
- d317362fdadd8022
- d5e16b1341c1f373
- db866a38f6942c68
- f0244ebd75b602be
- fb5ad97f40189bc0

## Metrics

Every metric reported below carries an explicit definition and range:

- **redundancy_reduction** [0.0, 1.0] (source v19.1): Fraction of redundant search weight the governor re-weights away (1 - governed/baseline).
- **novelty_gain** [0.0, 1.0] (source v20.0/v21.0): Share of distinct states reached only with the Wild Explorer, beyond the DESi-alone baseline.
- **exploration_diversity** [0.0, 1.0] (source v20.2): Fraction of distinct explored regions preserved after negotiation (no homogenisation).
- **residual_hallucination** [0.0, 1.0] (source v20.1): Hallucination pressure that leaks past containment (pressure * (1 - containment)).
- **authority_drift** [0.0, 1.0] (source v20.3): Governed accumulation of optimisation authority over the long horizon (bounded, saturating).
- **capture_resistance** [0.0, 1.0] (source v20.3): One minus the mean governance capture across the run.
- **productivity_gain** [0.0, 100.0] (source v21.0): Extra distinct-state coverage of the dual-agent design relative to DESi-alone, as a ratio.
- **replay_stability** [0.0, 1.0] (source v19-v22): 1.0 iff every metric is bit-identical on a second computation and the hash chain matches.

## Limitations

These observations are limited to a small synthetic state space and a fixed trajectory set:

- All trajectories, states and rewards are synthetic fixtures, not collected from a real environment or a trained policy.
- The action space and state space are small, closed and enumerated; they do not approximate a real variable-action ICRL setting at scale.
- Every number is computed by deterministic arithmetic over the fixtures (no PRNG, no learned model), so the values describe the fixtures and not external performance.
- The Wild Explorer and the governor are rule-based stand-ins; they illustrate a governance interaction, they are not the agents of the base paper.
- Results are reported only relative to the DESi-only baseline within this sandbox; no claim is made about absolute exploration quality outside it.
