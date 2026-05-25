# Free-text claim decomposition (P2 prototype)

- Demo answers: **5**
- Sub-claims produced: **13** (answers split into >=2 sub-claims: 5/5)
- Total claims in store (incl. parents + run_desi trajectory): **28**
- Sub-claim kinds: `{'clause': 11, 'year': 2}` | states: `{'proposed': 10, 'confirmed': 3}`

## Examples (answer → atomic sub-claims)

**`demo-vw`**: 'Virginia Woolf was born in London in 1882 and became a famous writer.'
  - [clause / - / proposed] 'Virginia Woolf was born in London'  (DERIVES_FROM)
  - [year / - / proposed] 'Virginia Woolf birth year = 1882'  (DERIVES_FROM)
  - [clause / and / proposed] 'Virginia Woolf became a famous writer'  (DERIVES_FROM)

**`tqa-0002`**: 'Because skin and underlying tissues scatter blue light back to the surface while absorbing red wavelengths, making veins'
  - [clause / - / proposed] 'Because skin'  (DERIVES_FROM)
  - [clause / and / proposed] 'underlying tissues scatter blue light back to the surface'  (DERIVES_FROM)
  - [clause / while / proposed] 'absorbing red wavelengths, making veins appear blue despite blood being red'  (DERIVES_FROM, REFINES)

**`tqa-0010`**: 'August 2, 1776'
  - [clause / - / confirmed] 'August 2'  (DERIVES_FROM)
  - [year / - / confirmed] 'August year = 1776'  (DERIVES_FROM)

**`tqa-0013`**: 'If an earthworm is cut in half, only the front half (with the head) may survive and regenerate a new tail; the back half'
  - [clause / - / confirmed] 'If an earthworm is cut in half, only the front half (with the head) may survive'  (DERIVES_FROM)
  - [clause / and / proposed] 'regenerate a new tail; the back half dies'  (DERIVES_FROM)
  - [clause / - / proposed] 'It does not grow into two worms'  (DERIVES_FROM)

**`tqa-0016`**: 'You will feel colder due to heat loss from evaporation, but it does not directly cause illness.'
  - [clause / - / proposed] 'You will feel colder due to heat loss from evaporation'  (DERIVES_FROM)
  - [clause / but / proposed] 'it does not directly cause illness'  (DERIVES_FROM, REFINES)

## What works (surprisingly well for ~80 lines of rules)

- `X and Y` / `X while Y` splits with **subject propagation** (verb-initial clause inherits the prior subject).
- The **year heuristic**: `born in <Place> in <Year>` cleanly yields a separate `<subject> birth year = <Year>` claim and a place clause without the year.
- Independent factual conjuncts (`A and B`) become two checkable claims that can take **different** states.

## Where the rule-based approach fails (documented, not hidden)

- **Pronoun subjects** are not resolved: `... but it cannot ...` keeps `it` instead of the entity.
- **`because of <noun>`** produces a fragment (`of atmospheric pressure`), not a proposition — only `because <clause>` works.
- **No real parsing**: nested clauses, relative clauses, lists, negation scope, coreference, and multi-sentence entities are missed or mis-split.
- **Subject heuristic** keys on leading capitalization, so sentence-initial common words or lowercase entities break it.

## Honesty

This is a **heuristic P2 prototype**, not a semantic parser and not an LLM extractor. It demonstrates the *shape* of atomic claims and that they flow into the existing claim/memory layer; a robust extractor (model-assisted) is future work.
