# DESi, explained simply (ELI5)

No background in AI, compilers, or systems theory needed. This keeps it
simple — but not *wrong*.

## The one-sentence idea

> A normal AI gives you **answers**.
> DESi watches and records the **path** along which statements are
> formed — and lets you replay and check that path later.

## A picture

Think of DESi as a **flight recorder (black box)**, a **lab notebook**,
and **version control for thinking**, combined:

- A **flight recorder** keeps an exact, tamper-evident record of what
  happened, so it can be reviewed afterwards.
- A **lab notebook** writes down each claim, the evidence for it, and
  what was uncertain — instead of only the final conclusion.
- **Version control** lets you re-run the exact same inputs and get the
  exact same result, and see what changed.

DESi does this for the *reasoning steps* of an AI pipeline.

## What DESi actually keeps track of

- **Claims** — the statements that were made.
- **Evidence** — what (if anything) supports each claim.
- **Conflicts and tensions** — where statements disagree or a story
  doesn't quite add up.
- **Uncertainty** — what was *not* known or *not* supported.
- **Replay traces** — a hash of each step so the same input always
  reproduces the same result, exactly.

## What DESi is **not**

- DESi is **not** a new language model. It has no chat box.
- DESi does **not** replace ChatGPT, Claude, or DeepSeek. It works
  *above* such models, checking and recording what they produce.
- DESi is **not** a general thinking machine and **not** a replacement
  for people, experts, or peer review.

## The honest part about hallucinations

DESi does **not** make hallucinations magically impossible. What it
does is make them **visible and checkable**: if a model says something
that isn't backed by evidence, DESi records that as an "ungrounded"
claim you can see — instead of letting it slip by unnoticed. Catching
something is not the same as preventing it, and DESi is honest about
that difference.

## Things DESi deliberately never claims

- It does **not** "solve truth."
- It does **not** prevent all hallucinations.
- It is **not** a general intelligence.
- It does **not** replace human judgement.

## Why "replay" matters

If you give DESi the same inputs twice, you get **byte-for-byte the
same output** — no randomness, no hidden state, no timestamps. That
sounds boring, but it's the whole point: a result you can reproduce and
audit is a result you can trust to *check*, the same way a scientist
expects an experiment to be repeatable.

## Where to go next

- Try it offline in 5 minutes: [QUICKSTART.md](../QUICKSTART.md)
- Install step by step: [INSTALL_DUMMIES.md](../INSTALL_DUMMIES.md)
- The full system paper: the repository `README.md`.

DESi is **experimental** software (version `0.1.0a0`). Treat its
results as exploratory.
