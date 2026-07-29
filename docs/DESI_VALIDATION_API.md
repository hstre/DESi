# DESi Validation API v0.1

This document specifies a read-only, deterministic interface for validating candidate state updates produced by memory and agent systems. MSCE is the first reference integration, but the contract is intentionally system-neutral.

## Architectural position

```text
L1 interaction traces
        |
        v
L2 policies
        |
        v
candidate L3 update
        |
        v
DESi validation interface (read-only)
        |
        +-- admissible
        +-- retained_as_hypothesis
        +-- requiring_further_verification
        +-- contradicted
        +-- rejected
```

DESi does not write to MSCE state. The calling system remains responsible for promotion, storage, rollback, and human approval.

## Core distinction

Operational success and epistemic warrant are separate signals:

```text
V_operational != V_epistemic
```

Repeated success can support a policy while leaving the inferred explanation, causal regularity, or applicability boundary unverified.

## Input contract

A candidate update contains:

- a stable candidate identifier;
- the proposed declarative claim;
- typed observations, inferences, and assumptions;
- supporting and contradicting evidence anchors;
- trace and policy provenance;
- a proposed applicability boundary;
- the intended target, such as `L3`.

Example:

```json
{
  "candidate_id": "msce-l3-001",
  "claim": "Tool X is reliable for bounded task class Y.",
  "items": [
    {
      "item_id": "obs-1",
      "item_type": "observation",
      "text": "Tool X completed 18 of 20 verified episodes.",
      "evidence_ids": ["ev-1"]
    },
    {
      "item_id": "inf-1",
      "item_type": "inference",
      "text": "Tool X is operationally reliable under the tested conditions.",
      "evidence_ids": ["ev-1"]
    }
  ],
  "evidence": [
    {
      "anchor_id": "ev-1",
      "source_id": "trace-batch-7",
      "content_hash": "sha256:abc",
      "locator": "episodes:1-20",
      "polarity": "support"
    }
  ],
  "source_trace_ids": ["trace-1", "trace-2"],
  "policy_ids": ["policy-9"],
  "applicability_boundary": "Only for task class Y under configuration C.",
  "proposed_target": "L3"
}
```

## Output contract

The validator returns one closed decision plus an auditable explanation:

```json
{
  "candidate_id": "msce-l3-001",
  "decision": "admissible",
  "reasons": ["structurally_supported_and_uncontradicted"],
  "required_verification": [],
  "supporting_evidence_ids": ["ev-1"],
  "counterevidence_ids": [],
  "input_hash": "...",
  "ruleset_version": "desi-validation-v0.1"
}
```

## Decision semantics

- `admissible`: structurally complete, supported, bounded, and not contradicted.
- `retained_as_hypothesis`: useful candidate containing an unresolved assumption.
- `requiring_further_verification`: incomplete support or applicability definition.
- `contradicted`: explicit counterevidence is present; promotion is blocked.
- `rejected`: malformed input, missing provenance, invalid references, or another contract failure.

These verdicts are governance outputs, not claims of truth.

## Running the reference implementation

No third-party dependencies are required.

```bash
python -m desi_validation.cli candidate.json
python -m unittest tests.test_validation_api
```

## MSCE integration point

At the L2-to-L3 boundary:

1. MSCE constructs a candidate update before committing L3 cognition.
2. `candidate_from_msce()` maps the MSCE object into the neutral contract.
3. `validate_candidate()` returns a deterministic verdict.
4. MSCE applies its own promotion policy based on that verdict.
5. The candidate, verdict, ruleset version, and input hash are retained for replay and audit.

A second gate can be applied before skill promotion using the same contract, with `proposed_target` set to `skill`.

## Current limits

Version 0.1 validates structural warrant, provenance completeness, explicit assumptions, applicability boundaries, and the presence of counterevidence. It does not yet determine whether a source is factually correct, whether a causal inference is valid, or whether two semantically different statements are actually contradictory. Those functions require explicit adapters or separately governed evaluators and must not be implied by this interface.
