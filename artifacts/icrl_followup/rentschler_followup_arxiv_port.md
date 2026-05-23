# Controlled Exploratory Pressure as a Read-Only Governance Layer for In-Context Exploration: A Synthetic Follow-Up to Rentschler and Roberts (2025)

## Abstract

We report a small, fully synthetic follow-up study on a read-only epistemic governance layer over an in-context reinforcement-learning-style exploration process, complementary to the base paper [Rentschler and Roberts, 2025]. On a closed synthetic state space, soft re-weighting of redundant trajectories reduced search redundancy while preserving novel-state reachability, and a generator/governor split increased distinct-state coverage. Every reported number is derived from a named sprint and is replay-exact. We make no claim beyond the sandbox.

## Introduction

The base paper [Rentschler and Roberts, 2025] studies in-context reinforcement learning for variable action spaces and skill stitching. We follow up one narrow question from its Section 4.6 discussion of limitations: can a separate, read-only governance layer mark redundancy and contain unsupported certainty without replacing the policy? This is an engineering study on a synthetic corpus, not a claim about learning systems in general.

## Related Work

This work is a complementary follow-up to the base paper [Rentschler and Roberts, 2025], which identifies several open in-context exploration problems in its Section 4.6 limitations. We address them with a read-only governance layer rather than a replacement for reinforcement learning.

- The base paper studies in-context reinforcement learning for variable action spaces and skill stitching. (rentschler_roberts_2025)
- The base paper notes, in its Section 4.6 limitations, open exploration problems: exploration collapse, sparse-reward failure and repetitive trajectories. (rentschler_roberts_2025)
- We position this work as a complementary follow-up to the base paper's open exploration question. (rentschler_roberts_2025)

## Problem Statement

Following the base paper [Rentschler and Roberts, 2025], we target three open exploration problems on a synthetic corpus: exploration collapse into repeated suboptimal behaviour, sparse-reward failure where the goal stays undiscovered, and repetitive trajectories that provide little new information.

## The DESi Governance Layer

In this paper, DESi denotes nothing more than a small, read-only governance layer over a synthetic exploration process; we use the name only as a local label and make no broader claim about it. Concretely, DESi is a generator/governor split: a generator agent proposes aggressive trajectories, and a governor reads them, classifies them by structure (not by reward) and assigns soft priority weights. The governor is read-only and non-authoritative: it never edits the policy, never injects reward, never deletes or pins a trajectory, and does not learn or optimise anything. DESi here is local to this synthetic study and complementary to reinforcement learning - not a replacement for it and not a general-purpose system - and we make no claim about it beyond this sandbox.

## Experimental Conditions

All trajectories, states and rewards are synthetic fixtures. Provenance of each result is named below (DESi-only baseline = v19, DESi + Wild Explorer = v20, comparison = v21).

- redundancy_reduction (source v19.1): DESi-only governance over a synthetic fixed trajectory set; soft re-weighting, no deletion.
- novelty_gain (source v20.0/v21.0): DESi + Wild Explorer; novelty contributed by the generator agent over the synthetic state space.
- residual_hallucination (source v20.1): Adversarial generator output; high-certainty incoherent paths capped by the governor.
- exploration_diversity (source v20.2): Negotiation layer; distinct regions preserved (no homogenisation), synthetic corpus.
- authority_drift (source v20.3): 5600-step deterministic dual-agent ecology; governed drift bounded by saturation.
- capture_resistance (source v20.3): Long-horizon ecology; governance capture held at zero across the run.
- productivity_gain (source v21.0): Comparison of dual-agent vs DESi-alone distinct-state coverage on the synthetic corpus.
- replay_stability (source v19-v22): Every metric computed twice and a deterministic hash chain recorded across all phases.

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

## Results

On the synthetic corpus, with each number derived from its named sprint:

- redundancy_reduction = 0.9 (derived in v19.1)
- novelty_gain = 0.733333 (derived in v20.0/v21.0)
- residual_hallucination = 0.0 (derived in v20.1)
- exploration_diversity = 1.0 (derived in v20.2)
- authority_drift = 0.088417 (derived in v20.3)
- capture_resistance = 1.0 (derived in v20.3)
- productivity_gain = 2.75 (derived in v21.0)
- replay_stability = 1.0 (derived in v19-v22)

## Discussion

Our reading of these synthetic results is deliberately narrow. Controlled exploratory pressure, implemented as a generator/governor split, may increase exploratory breadth in synthetic ICRL-style trajectory settings without increasing residual unsupported certainty, provided that the governance layer remains read-only, replay-stable, and non-authoritative. This is a hypothesis consistent with the sandbox measurements (novelty_gain = 0.733333, derived in v20.0/v21.0; residual_hallucination = 0.0, derived in v20.1), not a demonstrated property of real reinforcement-learning systems. Whether the effect holds outside this synthetic corpus, and under a trained policy, remains an open question that we do not address here [Rentschler and Roberts, 2025].

## Limitations

These observations are limited to a small synthetic state space and a fixed trajectory set:

- All trajectories, states and rewards are synthetic fixtures, not collected from a real environment or a trained policy.
- The action space and state space are small, closed and enumerated; they do not approximate a real variable-action ICRL setting at scale.
- Every number is computed by deterministic arithmetic over the fixtures (no PRNG, no learned model), so the values describe the fixtures and not external performance.
- The Wild Explorer and the governor are rule-based stand-ins; they illustrate a governance interaction, they are not the agents of the base paper.
- Results are reported only relative to the DESi-only baseline within this sandbox; no claim is made about absolute exploration quality outside it.

## Reproducibility Statement

Every metric is computed by deterministic arithmetic over fixed synthetic fixtures (no PRNG, no learned model). All 8 reported numbers are derived from a named sprint and recomputed bit-identically, with a deterministic hash chain recorded across phases (claim traceability 1.0). The study is replay-exact and scoped to the sandbox.

## Conclusion

As a complementary follow-up to the base paper's Section 4.6 open problems [Rentschler and Roberts, 2025], a read-only governance layer reduced redundant search and contained unsupported certainty while preserving novelty and remaining replay-exact on a small synthetic corpus. We present this as a narrow, reproducible engineering result and leave evaluation beyond the sandbox to future work.

## References

[1] Rentschler and Roberts (2025). In-Context Reinforcement Learning for Variable Action Spaces and Skill Stitching. arXiv:2501.14176.
