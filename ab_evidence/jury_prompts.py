"""Frozen prompts for the DESi-Jury pilot. Do NOT modify after the run starts."""

JURY_SYSTEM = (
    "You are a strict scientific grader evaluating a model's answer against a gold answer. "
    "You MUST respond with exactly three lines, no more, no less, in this format:\n"
    "Q1: <yes|partial|no>\n"
    "Q2: <answer|refusal|clarification|empty>\n"
    "Q3: <hallucination|absence|na>\n\n"
    "Definitions:\n"
    "- Q1: Does the MODEL ANSWER contain the information given in the GOLD ANSWER?\n"
    "    yes     = gold information is fully present\n"
    "    partial = gold information is touched on but incomplete or mixed with extras\n"
    "    no      = gold information is absent or contradicted\n"
    "- Q2: What kind of response is the MODEL ANSWER?\n"
    "    answer        = a substantive answer attempt\n"
    "    refusal       = 'I don't know' / 'I have no information' / decline to answer\n"
    "    clarification = asks the user for more info instead of answering\n"
    "    empty         = no content at all\n"
    "- Q3: Only if Q1 != yes. Is the wrong content hallucinated material or simply absent?\n"
    "    hallucination = invented facts that contradict or replace the gold\n"
    "    absence       = the answer lacks the gold info but doesn't invent new facts\n"
    "    na            = use this when Q1 = yes\n\n"
    "Respond with ONLY those three lines. No explanation, no preamble."
)


def build_user_message(question, gold, model_answer):
    return (
        f"QUESTION:\n{question}\n\n"
        f"GOLD ANSWER:\n{gold}\n\n"
        f"MODEL ANSWER:\n{model_answer or '(empty)'}"
    )


# Pre-registered concept-gate aggregation
def aggregate_jury(reviews):
    """Closed-enumeration aggregation. reviews is a list of dicts with q1, q2, q3.

    Rules:
      - All 3 reviewers say Q1=yes        -> score 1.0
      - >=2 reviewers say Q1 in {yes, partial} AND >=1 says partial -> score 0.5
      - >=2 reviewers say Q1=no           -> score 0.0
      - everything else                   -> score UNSURE (None)
    """
    q1s = [r.get("q1") for r in reviews if r.get("q1")]
    if len(q1s) < 3:
        return {"score": None, "verdict": "UNSURE", "reason": "fewer than 3 reviews"}
    yes = sum(1 for q in q1s if q == "yes")
    partial = sum(1 for q in q1s if q == "partial")
    no = sum(1 for q in q1s if q == "no")

    if yes == 3:
        return {"score": 1.0, "verdict": "CORRECT", "reason": "unanimous yes"}
    if no >= 2:
        return {"score": 0.0, "verdict": "WRONG", "reason": f"{no}/3 say no"}
    if (yes + partial) >= 2 and partial >= 1:
        return {"score": 0.5, "verdict": "PARTIAL", "reason": f"yes={yes} partial={partial} no={no}"}
    return {"score": None, "verdict": "UNSURE", "reason": f"dissent: yes={yes} partial={partial} no={no}"}


def parse_review(text):
    """Parse a reviewer response into structured {q1, q2, q3}. Returns dict; unknown values -> None."""
    out = {"q1": None, "q2": None, "q3": None, "raw": text}
    Q1_OK = {"yes", "partial", "no"}
    Q2_OK = {"answer", "refusal", "clarification", "empty"}
    Q3_OK = {"hallucination", "absence", "na"}
    for line in (text or "").splitlines():
        line = line.strip()
        low = line.lower()
        if low.startswith("q1:"):
            val = low.split(":", 1)[1].strip().split()[0] if ":" in low else ""
            if val in Q1_OK:
                out["q1"] = val
        elif low.startswith("q2:"):
            val = low.split(":", 1)[1].strip().split()[0] if ":" in low else ""
            if val in Q2_OK:
                out["q2"] = val
        elif low.startswith("q3:"):
            val = low.split(":", 1)[1].strip().split()[0] if ":" in low else ""
            if val in Q3_OK:
                out["q3"] = val
    return out
