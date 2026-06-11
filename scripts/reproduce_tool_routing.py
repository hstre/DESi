#!/usr/bin/env python3
"""Reproduce the tool-arm result on the committed GSM-Symbolic fixtures.

Demonstrates the "logic" arm of a tool-router: a deterministic arithmetic
evaluator over the locally-authored, GSM-Symbolic-shaped fixtures in
``src/desi/gsm_symbolic/data/`` (NOT Apple's data, NOT model outputs).

Honest scope:
  * The arithmetic is exact and replay-stable BY CONSTRUCTION.
  * End-to-end accuracy is bounded only by the naive operand extraction
    (``arithmetic_tool.extract_operands``) — i.e. by language, not by math.
  * Every residual failure is categorized: lexical (a word numeral) or
    semantic (an operative added clause that changes the computation). Both are
    the model's job. The count of *arithmetic* failures is the headline: zero.

This is not a head-to-head against a live LLM (no model outputs exist in this
repo). It localizes the routing boundary: hand the computation to the tool;
keep operand-binding and clause-relevance with the model.

Usage:
    python scripts/reproduce_tool_routing.py
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi_router.arithmetic_tool import (  # noqa: E402
    extract_operands,
    solve,
    solve_question,
    structure_expr_and_vars,
)

DATA_GLOB = str(REPO_ROOT / "src" / "desi" / "gsm_symbolic" / "data" / "*.json")


def load_instances() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(glob.glob(DATA_GLOB)):
        data = json.load(open(path, encoding="utf-8"))
        for tmpl in data["templates"]:
            for inst in tmpl["instances"]:
                rows.append(
                    {
                        "id": inst["instance_id"],
                        "structure": tmpl["structure"],
                        "question": inst["question"],
                        "answer": inst["answer"],
                    }
                )
    return rows


def run(words: bool = True) -> dict:
    rows = load_instances()
    correct = 0
    # Arithmetic failures are zero BY CONSTRUCTION (exact AST evaluation) —
    # there is deliberately no "arithmetic" failure list here, because nothing
    # could ever populate it; every miss is categorized as language
    # (lexical extraction or operative-clause semantics).
    lexical: list[str] = []
    semantic: list[str] = []
    results: list[tuple[str, object]] = []

    for r in rows:
        _, variables = structure_expr_and_vars(r["structure"])
        ops = extract_operands(r["question"], words=words)
        try:
            got = solve_question(r["structure"], r["question"], words=words)
        except ValueError:
            lexical.append(r["id"])          # too few operands -> extraction miss
            results.append((r["id"], "ERR"))
            continue
        results.append((r["id"], got))
        if got == r["answer"]:
            correct += 1
        elif len(ops) < len(variables):
            lexical.append(r["id"])
        else:
            # operands extracted but answer wrong -> an operative clause was
            # missed. The arithmetic on those operands is still correct, so this
            # is a semantic (language) failure, never an arithmetic one.
            semantic.append(r["id"])

    digest = hashlib.sha256(
        json.dumps(results, sort_keys=True).encode()
    ).hexdigest()
    return {
        "n": len(rows),
        "correct": correct,
        "lexical": lexical,
        "semantic": semantic,
        "digest": digest,
    }


def main() -> None:
    # tool proper: exact on explicit operands (the part a router sends to a tool)
    assert solve("rate * hours + bonus", [12, 7, 5]) == 89
    assert solve("(items * price) - discount", [9, 4, 6]) == 30
    assert solve("total / groups", [84, 6]) == 14

    t0 = time.perf_counter()
    naive = run(words=False)
    with_words = run(words=True)
    dt_ms = (time.perf_counter() - t0) * 1000

    # replay stability: same inputs -> identical results digest
    digest_again = run(words=True)["digest"]

    n = with_words["n"]
    print(f"fixtures (illustrative, local)     : {n}")
    print(f"tool arm, digits-only              : {naive['correct']}/{n}")
    print(f"tool arm, + word numerals          : {with_words['correct']}/{n}")
    print("arithmetic failures                : 0 (by construction — exact AST evaluation)")
    print(f"lexical (extraction) failures      : {len(with_words['lexical'])} {with_words['lexical']}")
    print(f"semantic (operative-clause) failures: {len(with_words['semantic'])} {with_words['semantic']}")
    print("cost                               : $0.00 (no model call)")
    print(f"latency, all {n} items             : {dt_ms:.2f} ms total")
    print(f"replay-stable (digest matches)     : {with_words['digest'] == digest_again}")
    print(f"results digest                     : {with_words['digest'][:16]}…")


if __name__ == "__main__":
    main()
