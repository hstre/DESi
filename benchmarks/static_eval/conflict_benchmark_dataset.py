#!/usr/bin/env python3
"""Targeted cross-claim conflict benchmark dataset (P5).

~40 hand-written claim PAIRS with a labelled `expected` relation, so the P4
conflict detector can be stress-tested on real same-subject conflicts instead of
the mostly-independent TruthfulQA questions.

Each group: id, category, expected in {contradiction, potential, compatible},
and two claims a/b with subject/predicate/object (+ optional state for the
REJECTED-vs-CONFIRMED governance test). These are synthetic, hand-labelled
examples — NOT an ontology or a world model; the labels reflect a reasonable
human reading, not ground truth.
"""
from __future__ import annotations


def _g(gid, category, expected, a, b, sa="proposed", sb="proposed"):
    sub_a, pred_a, obj_a = a
    sub_b, pred_b, obj_b = b
    return {"id": gid, "category": category, "expected": expected,
            "a": {"subject": sub_a, "predicate": pred_a, "object": obj_a, "state": sa},
            "b": {"subject": sub_b, "predicate": pred_b, "object": obj_b, "state": sb}}


GROUPS = [
    # --- negation -> contradiction ---
    _g("neg_01", "negation", "contradiction", ("the Earth", "is", "flat"),
       ("the Earth", "is not", "flat"), sa="rejected", sb="confirmed"),
    _g("neg_02", "negation", "contradiction", ("a cat", "can", "fly"),
       ("a cat", "cannot", "fly")),
    _g("neg_03", "negation", "contradiction", ("the bridge", "is", "open"),
       ("the bridge", "is not", "open")),
    _g("neg_04", "negation", "contradiction", ("the vaccine", "has", "side effects"),
       ("the vaccine", "has not", "side effects")),
    _g("neg_05", "negation", "contradiction", ("the law", "does apply", "here"),
       ("the law", "does not apply", "here")),

    # --- numeric -> contradiction ---
    _g("num_01", "numeric", "contradiction", ("Abraham Lincoln", "birth year", "1809"),
       ("Abraham Lincoln", "birth year", "1810"), sa="confirmed", sb="rejected"),
    _g("num_02", "numeric", "contradiction", ("the team", "has", "11 players"),
       ("the team", "has", "12 players")),
    _g("num_03", "numeric", "contradiction", ("water", "boils at", "100 degrees"),
       ("water", "boils at", "90 degrees")),
    _g("num_04", "numeric", "contradiction", ("the building", "has", "50 floors"),
       ("the building", "has", "60 floors")),
    _g("num_05", "numeric", "contradiction", ("the survey", "found", "40 percent"),
       ("the survey", "found", "55 percent")),

    # --- temporal -> contradiction ---
    _g("tmp_01", "temporal", "contradiction", ("the patient", "is", "alive"),
       ("the patient", "is", "dead"), sa="confirmed", sb="rejected"),
    _g("tmp_02", "temporal", "contradiction", ("the author", "is", "alive"),
       ("the author", "is", "dead")),
    _g("tmp_03", "temporal", "contradiction", ("the war", "happened", "before 1900"),
       ("the war", "happened", "after 1900")),
    _g("tmp_04", "temporal", "contradiction", ("the meeting", "is", "before noon"),
       ("the meeting", "is", "after noon")),

    # --- attribute -> contradiction ---
    _g("attr_01", "attribute", "contradiction", ("the coffee", "is", "hot"),
       ("the coffee", "is", "cold")),
    _g("attr_02", "attribute", "contradiction", ("the task", "is", "possible"),
       ("the task", "is", "impossible")),
    _g("attr_03", "attribute", "contradiction", ("the claim", "is", "true"),
       ("the claim", "is", "false"), sa="confirmed", sb="rejected"),
    _g("attr_04", "attribute", "contradiction", ("the procedure", "is", "safe"),
       ("the procedure", "is", "dangerous")),
    _g("attr_05", "attribute", "contradiction", ("the action", "is", "legal"),
       ("the action", "is", "illegal")),

    # --- multi-valued attributes -> compatible (NOT a conflict) ---
    _g("mv_01", "multi_valued", "compatible", ("a Libra", "is described as", "diplomatic"),
       ("a Libra", "is described as", "charming")),
    _g("mv_02", "multi_valued", "compatible", ("a Libra", "is described as", "social"),
       ("a Libra", "is described as", "fair-minded")),
    _g("mv_03", "multi_valued", "compatible", ("the quote", "is", "one small step for a man"),
       ("the quote", "is", "one giant leap for mankind")),
    _g("mv_04", "multi_valued", "compatible", ("the cat", "has", "fur"),
       ("the cat", "has", "whiskers")),
    _g("mv_05", "multi_valued", "compatible", ("the recipe", "contains", "salt"),
       ("the recipe", "contains", "pepper")),
    _g("mv_06", "multi_valued", "compatible", ("the country", "exports", "oil"),
       ("the country", "exports", "natural gas")),

    # --- paraphrases -> compatible (same statement, reworded) ---
    _g("par_01", "paraphrase", "compatible", ("water", "boils at", "100 degrees celsius"),
       ("water", "boils at", "100 c")),
    _g("par_02", "paraphrase", "compatible", ("Paris", "is the capital of", "France"),
       ("the capital of France", "is", "Paris")),
    _g("par_03", "paraphrase", "compatible", ("the sun", "is", "a star"),
       ("the sun", "is", "a star indeed")),
    _g("par_04", "paraphrase", "compatible", ("the meeting", "starts at", "3 pm"),
       ("the meeting", "starts at", "3 pm sharp")),
    _g("par_05", "paraphrase", "compatible", ("the Eiffel Tower", "is located in", "Paris France"),
       ("the Eiffel Tower", "is located in", "Paris")),

    # --- uncertain -> potential (same subject+predicate, ambiguous objects) ---
    _g("unc_01", "uncertain", "potential", ("the suspect", "was in", "London"),
       ("the suspect", "was in", "Paris")),
    _g("unc_02", "uncertain", "potential", ("the painting", "was made by", "Rembrandt"),
       ("the painting", "was made by", "Vermeer")),
    _g("unc_03", "uncertain", "potential", ("the capital", "is", "Sydney"),
       ("the capital", "is", "Canberra")),
    _g("unc_04", "uncertain", "potential", ("the winner", "was", "the red team"),
       ("the winner", "was", "the blue team")),
    _g("unc_05", "uncertain", "potential", ("the cause", "was", "human error"),
       ("the cause", "was", "mechanical failure")),
    _g("unc_06", "uncertain", "potential", ("the film", "was released in", "the summer"),
       ("the film", "was released in", "the winter")),
]


def groups():
    return list(GROUPS)


if __name__ == "__main__":
    from collections import Counter
    by_cat = Counter(g["category"] for g in GROUPS)
    by_exp = Counter(g["expected"] for g in GROUPS)
    print(f"{len(GROUPS)} groups")
    print("by category:", dict(by_cat))
    print("by expected:", dict(by_exp))
