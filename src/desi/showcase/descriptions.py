"""Hand-crafted descriptions per showcase scenario.

The descriptions are intentionally written in plain technical language.
No marketing claims. Each field is a single short paragraph that a
reviewer can read without context from the rest of the codebase.

These strings are inserted verbatim into the generated ``analysis.md``
and ``baseline_notes.md`` artefacts.
"""
from __future__ import annotations


SHOWCASE_IDS: tuple[str, ...] = ("S2", "S6", "S7")


SHOWCASE_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "S2": {
        "title": "Contradiction Detection",
        "goal": "DESi recognises a genuine epistemic conflict between "
                "two hypotheses on the same parent claim.",
        "problem":
            "Two hypothesis_builder operations (T6) produce competing "
            "claims C002 and C003 on top of C001. Both are followed by "
            "an explicit make-conflict-explicit step (T2). A system that "
            "averages or smooths over these would collapse the two into "
            "one mid-confidence aggregate. A system that detects "
            "contradictions cleanly leaves both claims standing and "
            "records the conflict as a structural fact in the graph.",
        "why_relevant":
            "Contradiction-tolerance is the load-bearing case for an "
            "epistemic diagnostic system: without a stable record that "
            "two propositions are in conflict, every downstream "
            "decision is forced to pick one and hide the other. The "
            "v0.2 relation enum carries CONTRADICTS for exactly this "
            "reason; v0.4 surfaces it as part of the timeline so a "
            "reviewer can see when and where the conflict was acknowledged.",
        "classical_path":
            "A typical LLM run on the same input would either select "
            "one hypothesis (silent suppression of the other), or "
            "produce a hedged synthesis sentence that mentions both "
            "without separating them in any retrievable structure. "
            "The conflict, if present in the output, lives only in "
            "the prose surface and cannot be queried later.",
        "desi_path":
            "DESi keeps both claims as distinct nodes in the memory "
            "graph. Two CONTRADICTS edges (one per direction) are "
            "recorded in the end-state graph and emitted as "
            "relation_created timeline events. A reviewer can read "
            "the final graph, find C002 and C003 still present, and "
            "see the conflict relation in the Cypher export.",
    },
    "S6": {
        "title": "False Merge Rejection",
        "goal": "DESi resists merging two surface-similar but "
                "methodologically distinct claims.",
        "problem":
            "C_alpha and C_alpha_prime share most of their content "
            "tokens (the names alone differ by one suffix), and both "
            "received a T6/T3 derivation path. The temptation to "
            "merge them is high — they look like the same hypothesis. "
            "But the methodological provenance has not been checked "
            "for equivalence, and a merge here would collapse two "
            "distinct claim histories into one with a falsely-unified "
            "version chain.",
        "why_relevant":
            "Premature merging is the inverse failure mode of "
            "premature splitting: a system that always merges similar "
            "things loses the ability to detect that two paths agreed "
            "by accident. v0.2 introduced merge_claims as an atomic "
            "operation precisely so that a guard could refuse it. "
            "v0.4.1 makes the refusal externally visible.",
        "classical_path":
            "A classical LLM would normally compress C_alpha and "
            "C_alpha_prime into a single claim during a summary pass. "
            "The collapse leaves no record of the two source paths; "
            "the reader cannot tell after the fact that there was a "
            "decision to merge.",
        "desi_path":
            "DESi's guard inspects the surface similarity and "
            "explicitly refuses the merge with a recorded reason: "
            "``surface_similarity_only; methodological_distinctness_"
            "unverified``. The end-state graph contains no MERGED_INTO "
            "edge between the two claims; the timeline contains one "
            "guard_blocked event with the refusal reason in its "
            "payload.",
    },
    "S7": {
        "title": "Memory Trap",
        "goal": "DESi does not silently inherit a stale, "
                "method-weak claim from prior memory state.",
        "problem":
            "A legacy claim with content ``C_legacy`` and method "
            "``hearsay`` exists in the recorder from an earlier run. "
            "The current trajectory creates a new claim with the same "
            "content but produces it via a T6/T3 derivation. A system "
            "that deduplicates by content alone would collapse the new "
            "claim into the old one, silently inheriting the weaker "
            "method tag — and erasing the new derivation.",
        "why_relevant":
            "Memory bias is the failure mode where past confidence "
            "leaks forward into present judgement. The v0.1 Claim "
            "object separates content from method specifically so "
            "that two claims sharing content but produced differently "
            "stay distinct. v0.4.1 demonstrates that separation under "
            "a deliberately adversarial seeding.",
        "classical_path":
            "A classical retrieval-augmented LLM would surface the "
            "old claim as context for the new query, then either "
            "directly quote it (re-asserting hearsay) or write a new "
            "answer that reuses the old framing because the retrieval "
            "primed it. The fact that the new derivation was stronger "
            "than the old one is lost.",
        "desi_path":
            "DESi's recorder keeps the legacy claim (claim_id "
            "``C_legacy_old``, method ``hearsay``) and the newly "
            "produced claim (claim_id ``C_legacy``, method ``T6``) as "
            "two distinct nodes. Both appear in the end-state graph. "
            "The end-state JSON lists two claims with content "
            "``C_legacy`` carrying different methods; neither was "
            "silently overwritten or hidden.",
    },
}
