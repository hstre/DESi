# paper0 — Role-Prefix-Policy Falsification

**Status**: EXPLORATORY. Static (no-LLM) structural falsification of the
DESi Role-Prefix Policy as adopted in commit `e17efd8` of branch
`claude/init-desi-prototype-2QjHF`.

## Scope

The Role-Prefix Policy mandates that every DESi LLM role is a full epistemic
prefix prompt with seven fields (objective, allowed evidence, forbidden
inferences, acceptance criteria, exploratory-flag policy, output format,
anti-overclaiming guardrails) plus six global constraints.

This paper falsifies the *prefix text itself*, not the LLM behaviour produced
by it. The question we answer here is: **assuming a competent LLM that
literally follows every line of its prefix, does the prefix already protect
the system from the failures the project charter cares about?**

We do **not** call DeepSeek in this paper. Live-LLM falsification (whether a
real model in fact follows the prefix) is a separate, paid pass; see
`open-questions.md` if it materialises.

## Method

1. Inventory the protections each prefix actually states (`probes.md`,
   "Defence text in prefix" column).
2. For each role, enumerate adversarial probe payloads designed to slip past
   the prefix or expose ambiguity (`probes.md`, "Probe" column).
3. Predict the outcome under a strict-reading LLM (`probes.md`, "Predicted
   outcome").
4. Mark each probe as **HOLDS**, **AMBIGUOUS**, or **LEAKS**.
5. Aggregate into `findings.md` with required prefix revisions.

Probe count: 13 (≥10 as per the project's falsification cadence).

## Falsification cadence (DESi house style)

| Pass | Target | n | Branch |
|---|---|---:|---|
| (prior, chat-only) | deterministic detectors | 10 | `claude/init-desi-prototype-2QjHF` (fixtures committed in `6b999b5`) |
| **paper0 (this)** | role-prefix policy text | 13 | `paper0/role-policy-falsification` |
| (future) | live role behaviour (LLM-in-the-loop) | TBD | TBD |

## Branch policy

This work lives on `paper0/role-policy-falsification`. It must not be merged
into `main` until at least one live-LLM falsification pass replicates or
contradicts the structural predictions below.

## Scientific guardrails (inherited from the DESi charter)

- Findings here are **structural predictions**, not empirical claims.
- A probe marked HOLDS means the prefix *text* defends against the attack;
  it does **not** mean the LLM will defend in practice.
- A probe marked LEAKS means the prefix *text* is silent or ambiguous about
  the attack; a competent LLM may still defend, but the prefix does not
  compel it to.
- Small-n (13 probes, one author) — treat all results as EXPLORATORY.
