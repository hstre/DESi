# Citation Appendix - A Read-Only Governance Layer for In-Context Exploration: A Small Synthetic Follow-Up Study

## Citation Map

Each external claim is bound to a registered reference (citation as edge):

- EC1 -> [Rentschler and Roberts, 2025] (arXiv:2501.14176)
- EC2 -> [Rentschler and Roberts, 2025] (arXiv:2501.14176)
- EC3 -> [Rentschler and Roberts, 2025] (arXiv:2501.14176)

## Limitations

These observations are limited to a small synthetic state space and a fixed trajectory set:

- All trajectories, states and rewards are synthetic fixtures, not collected from a real environment or a trained policy.
- The action space and state space are small, closed and enumerated; they do not approximate a real variable-action ICRL setting at scale.
- Every number is computed by deterministic arithmetic over the fixtures (no PRNG, no learned model), so the values describe the fixtures and not external performance.
- The Wild Explorer and the governor are rule-based stand-ins; they illustrate a governance interaction, they are not the agents of the base paper.
- Results are reported only relative to the DESi-only baseline within this sandbox; no claim is made about absolute exploration quality outside it.

## References

[1] Rentschler and Roberts (2025). In-Context Reinforcement Learning for Variable Action Spaces and Skill Stitching. arXiv:2501.14176.
