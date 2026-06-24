"""Identical follow-up task per case — the SAME question is asked to both variants.

The follow-up is designed so the answer must touch the active state (decisions, constraints,
conflicts, open questions). Differential failures between A and B will be epistemic, not stylistic.
"""

FOLLOW_UPS = {
    "case1_architecture": (
        "Summarize the current state of the architecture in exactly this format, using only what we "
        "have established. Use short bullet points (max one line each). Do not invent anything. If a "
        "category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, DECISIONS "
        "TAKEN, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: "
        "given this state, what is the single most important next decision we still owe?"
    ),
    "case2_research": (
        "Summarize the current state of the analysis in exactly this format, using only what we have "
        "established. Use short bullet points (max one line each). Do not invent anything. If a "
        "category has no entries, write 'none'. The categories are: WORKING HYPOTHESIS, RULED OUT, "
        "QUASI-CONTROLS USED, OPEN CONFLICTS, OPEN QUESTIONS, EXTERNAL-COMMS GUARDRAILS. Then in a "
        "final line answer: what concrete evidence would change the working hypothesis?"
    ),
    "case3_debugging": (
        "Summarize the current state of the debugging effort in exactly this format, using only what "
        "we have established. Use short bullet points (max one line each). Do not invent anything. If "
        "a category has no entries, write 'none'. The categories are: CONFIRMED ROOT CAUSE, DECIDED "
        "FIXES, NOT YET VERIFIED, OPEN CONFLICTS, OPEN QUESTIONS, REJECTED OPTIONS. Then in a final "
        "line answer: what single check must happen before the cache fix ships?"
    ),
    "case4_long_research": (
        "Summarize the current state of the graph-processing system design in exactly this format, "
        "using only what we have established. Use short bullet points (max one line each). Do not "
        "invent anything. If a category has no entries, write 'none'. The categories are: ACTIVE "
        "CONSTRAINTS, ARCHITECTURE DECISIONS, REJECTED / REPLACED DIRECTIONS, OPEN CONFLICTS, OPEN "
        "QUESTIONS, ESTABLISHED CLAIMS, GATING ITEMS BEFORE PRODUCTION. Then in a final line answer: "
        "given this state, what is the single most important gating item we must resolve before any "
        "production commitment?"
    ),
    "case5_long_research": (
        "Summarize the current state of the graph-processing system design in exactly this format, "
        "using only what we have established. Use short bullet points (max one line each). Do not "
        "invent anything. If a category has no entries, write 'none'. The categories are: ACTIVE "
        "CONSTRAINTS, ARCHITECTURE DECISIONS, REJECTED / REPLACED DIRECTIONS, OPEN CONFLICTS, OPEN "
        "QUESTIONS, ESTABLISHED CLAIMS, GATING ITEMS BEFORE PRODUCTION. Then in a final line answer: "
        "given this state, what is the single most important gating item we must resolve before any "
        "production commitment?"
    ),
    "case6_long_research": (
        "Summarize the current state of the graph-processing system design in exactly this format, "
        "using only what we have established. Use short bullet points (max one line each). Do not "
        "invent anything. If a category has no entries, write 'none'. The categories are: ACTIVE "
        "CONSTRAINTS, ARCHITECTURE DECISIONS, REJECTED / REPLACED DIRECTIONS, OPEN CONFLICTS, OPEN "
        "QUESTIONS, ESTABLISHED CLAIMS, GATING ITEMS BEFORE PRODUCTION. Then in a final line answer: "
        "given this state, what is the single most important gating item we must resolve before any "
        "production commitment?"
    ),
    "case7a_padded_30k": (
        "Summarize the current state of the graph-processing system design in exactly this format, "
        "using only what we have established. Use short bullet points (max one line each). Do not "
        "invent anything. If a category has no entries, write 'none'. The categories are: ACTIVE "
        "CONSTRAINTS, ARCHITECTURE DECISIONS, REJECTED / REPLACED DIRECTIONS, OPEN CONFLICTS, OPEN "
        "QUESTIONS, ESTABLISHED CLAIMS, GATING ITEMS BEFORE PRODUCTION. Then in a final line answer: "
        "given this state, what is the single most important gating item we must resolve before any "
        "production commitment?"
    ),
    "case7b_padded_60k": (
        "Summarize the current state of the graph-processing system design in exactly this format, "
        "using only what we have established. Use short bullet points (max one line each). Do not "
        "invent anything. If a category has no entries, write 'none'. The categories are: ACTIVE "
        "CONSTRAINTS, ARCHITECTURE DECISIONS, REJECTED / REPLACED DIRECTIONS, OPEN CONFLICTS, OPEN "
        "QUESTIONS, ESTABLISHED CLAIMS, GATING ITEMS BEFORE PRODUCTION. Then in a final line answer: "
        "given this state, what is the single most important gating item we must resolve before any "
        "production commitment?"
    ),
    "case_s1_lifecycle": (
        "Summarize the CURRENT state of the rollout in exactly this format, using only what holds "
        "NOW. Do NOT report anything that was later reversed, ruled out, or superseded. Use short "
        "bullet points (max one line each). If a category has no entries, write 'none'. The "
        "categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, "
        "ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the "
        "single most important thing we must decide next?"
    ),
    "case_s2_lifecycle": (
        "Summarize the CURRENT state of the v1 API design in exactly this format, using only what "
        "holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or "
        "superseded. Use short bullet points (max one line each). If a category has no entries, "
        "write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, "
        "OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, "
        "what is the single most important thing we must decide next?"
    ),
    "case_s3_ml_lifecycle": (
        "Summarize the CURRENT state of the model-training effort in exactly this format, using only what holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or superseded. Use short bullet points (max one line each). If a category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the single most important thing we must decide next?"
    ),
    "case_s4_incident_lifecycle": (
        "Summarize the CURRENT state of the incident response in exactly this format, using only what holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or superseded. Use short bullet points (max one line each). If a category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the single most important thing we must decide next?"
    ),
    "case_s5_pricing_lifecycle": (
        "Summarize the CURRENT state of the pricing decision in exactly this format, using only what holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or superseded. Use short bullet points (max one line each). If a category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the single most important thing we must decide next?"
    ),
    "case_s6_pipeline_lifecycle": (
        "Summarize the CURRENT state of the data pipeline design in exactly this format, using only what holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or superseded. Use short bullet points (max one line each). If a category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the single most important thing we must decide next?"
    ),
    "case_s7_security_lifecycle": (
        "Summarize the CURRENT state of the auth security design in exactly this format, using only what holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or superseded. Use short bullet points (max one line each). If a category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the single most important thing we must decide next?"
    ),
    "case_s8_mobile_lifecycle": (
        "Summarize the CURRENT state of the mobile release plan in exactly this format, using only what holds NOW. Do NOT report anything that was later reversed, ruled out, deprecated, or superseded. Use short bullet points (max one line each). If a category has no entries, write 'none'. The categories are: ACTIVE CONSTRAINTS, CURRENT DECISIONS, OPEN CONFLICTS, OPEN QUESTIONS, ESTABLISHED CLAIMS. Then in a final line answer: given the current state, what is the single most important thing we must decide next?"
    ),
}
