# Widerspruchsbericht — MarCognity / Muse Spark 1.1

*Auto-generiert von `python -m desi.case_studies.marcognity_muse_spark`. Die drei strukturellen Widersprüche werden von DESis eigenem Detektor `desi.self_audit.contradictions.find_contradictions` gefunden, nicht von Prosa behauptet.*

## C1 — Method says 'no instructions' — the prompt demands them

- **Scope (Detektor):** `document:muse`
- **Konfligierende Werte:** 'none: no verification/sources/stages', 'required: >=5 references, direct citations, citation-check, six phases'
- **Claim-IDs (Detektor):** cl_04cc6b9fc834, cl_c859e464e204

The Method section (muse:L206) states the model got no requests for verification, sources, or stages. The printed prompt demands >=5 scientific references with direct citations (muse:L56-58), a citation-consistency check (muse:L64), database searches (muse:L24-27) and six named Phases (muse:L29-47). The experiment contradicts its own setup.

## C2 — All claims 'VERIFIED' — yet 'no citations found or verifiable'

- **Scope (Detektor):** `document:muse`
- **Konfligierende Werte:** 'no: no citations found or verifiable', 'yes: five claims VERIFIED'
- **Claim-IDs (Detektor):** cl_5e7a6e6d0fbd, cl_db18c12e7694

The report marks all five sampled claims STATUS: VERIFIED against 'the PubMed document' (muse:L170-198), while the same report ends 'No citations found or verifiable in the text' (muse:L201-202). The text nonetheless lists eight references (muse:L154-161). The two verdicts are mutually inconsistent — they come from two subsystems concatenated without reconciliation (code:agent_metacognition L48-66).

## C3 — 'Independent external validator' — actually one LLM over the generation context

- **Scope (Detektor):** `artifact:marcognity_validator`
- **Konfligierende Werte:** 'independent external validator', 'single LLM call over the generation retrieval context'
- **Claim-IDs (Detektor):** cl_4031c819c67d, cl_72bf188969e6

The Method calls MarCognity an 'independent external validator' (muse:L208; muse:L10). The implementation is a single llm.invoke call (code:skeptical_agent L62) that receives 'the reference documents used for generation' (code:evaluator_prompt L24-28). Independence is asserted; the code and the README (doc:readme L133) say the evaluator shares the generation context and may share biases.

## Selbstabdichtung (Aufgabe 7)

**Self-sealing:** True — Both a working and a failing validator are interpreted as confirming the Epistemic Boundary, and no outcome is designated as disconfirming. As run, the hypothesis is self-sealing. (MarCognity's own Boundary doc is more careful — doc:epistemic_boundary L119-122 asks for controlled validation — so the self-sealing is in the forum conclusion, not necessarily the underlying construct.)

**Was würde die Hypothese stützen?**
- Validator flags unverifiable claims -> the confidence/verifiability gap is 'made visible' (the stated goal).
- Validator fails / mis-attributes sources -> read as the Boundary 'even within the validator' (muse:L237).

**Was würde sie schwächen?**
- A pre-registered outcome where the validator, given domain-correct sources, verifies claims with quoted passages — NOT provided.

**Was würde sie widerlegen?**
- A control showing the residual failures vanish under proper source-gating and provenance (i.e. the failures are a pipeline defect, not an 'intrinsic architecture' property) — NOT provided.

**Falsifikationsbedingungen im Originalversuch angegeben?** nein.
