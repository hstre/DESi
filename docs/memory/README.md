# DESi memory layer (v0.1)

A structured, persistent claim graph for DESi. The layer is **observation-
only**: it stores what DESi produces and lets guards read from it, but
operators must not change their behaviour based on memory state in this
release. The contract is reproducibility, not self-modification.

## Modules

```
src/desi/memory/
  __init__.py        public API: Claim, Provenance, ClaimState,
                     Relation, RelationType, Run, OperatorEvent,
                     MemoryStore (protocol), InMemoryStore, Neo4jStore,
                     Neo4jDriverNotInstalled
  claim.py           Claim + Provenance + ClaimState
  relations.py       Relation + RelationType enum
  events.py          Run + OperatorEvent
  store.py           MemoryStore protocol + InMemoryStore + Neo4jStore
```

## Claim object

A Claim separates **what** (`content`) from **how** (`method`). Two claims
with the same content but different methods are different claims by
design — collapsing them would erase derivation history.

```python
from desi.memory import Claim, ClaimState, Provenance

claim = Claim(
    content="Water boils at 100C at sea-level pressure.",
    method="T6[hypothesis_builder]",
    state=ClaimState.PROPOSED,
    confidence=0.8,
    version=1,
    provenance=Provenance(
        source="des_v0.1",
        run_id="run_2026_05_14_xyz",
        operator_path=("T6",),
    ),
)
```

`claim_id` is derived deterministically from `content + method + run_id`
if not supplied, so the same input always maps to the same id.

## Relations

The six v0.1 relation types are closed by design:

| Type           | Direction      | Meaning                                  |
|---             |---             |---                                       |
| `SUPPORTS`     | source→target  | positive evidence                        |
| `CONTRADICTS`  | source→target  | incompatible                             |
| `REFINES`      | source→target  | more specific version                    |
| `DERIVES_FROM` | source→target  | source produced by operator on target    |
| `MERGED_INTO`  | source→target  | merge: source state becomes MERGED       |
| `SPLIT_FROM`   | source→target  | split: target state becomes SPLIT        |

New relation kinds require a code change. Free-form strings are
intentionally not accepted because guards rely on closed enumeration
semantics.

## Stores

`InMemoryStore` is the dependency-free default. It is sufficient for
tests and for DESi runs that do not need cross-run persistence.

`Neo4jStore` is opt-in. It requires the `neo4j` driver package
(`pip install -r requirements-memory.txt`). Constructing it without
the driver raises `Neo4jDriverNotInstalled` — DESi itself does not
import `neo4j` at module load time, so a missing driver does not
break local runs.

```python
from desi.memory import Neo4jStore

store = Neo4jStore(uri="bolt://localhost:7687",
                   auth=("neo4j", "password"))
store.add_claim(claim)
```

## Observation-only contract

The store is intentionally read/write but not "read-then-modify". The
contract is enforced socially in v0.1:

1. Guards may call `MemoryStore.get_claim`, `relations_for`,
   `all_claims`, etc.
2. Operators must not condition their output on memory state.
3. If an operator needs memory state to decide what to do, that is a
   v0.2 design question, not a v0.1 implementation question. Open it
   as a design issue rather than wiring it up silently.

This contract exists because a memory layer that operators consult is
no longer a memory layer; it is a control surface, and a control
surface needs a falsification protocol before it can be allowed to
change DESi's behaviour.

## What's deliberately out of scope in v0.1

- No automatic claim merge or split. The store records merges and
  splits via state transitions plus relations, but does not infer
  them.
- No similarity-based claim deduplication. Two claims with identical
  content but different methods stay distinct.
- No vector indices, embeddings, or semantic search.
- No write hooks into DESi's existing operators or diagnostics; the
  existing 13 tests on `claude/init-desi-prototype-2QjHF` are
  unchanged. (The release branch's experiment suite still passes
  separately on its own branch.)
