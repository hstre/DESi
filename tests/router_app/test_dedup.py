"""Prior-work lookup: content/method dedup and exact reuse across instances."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi import engine  # noqa: E402
from desi.dedup import (  # noqa: E402
    content_hash,
    method_class,
    method_hash,
    normalize_query,
)
from desi.ledger import Ledger  # noqa: E402
from desi.providers import load_config  # noqa: E402
from desi.tool_registry import default_registry  # noqa: E402

CONFIG = REPO_ROOT / "desi" / "config.example.json"


def _reg():
    return load_config(CONFIG)


# ---- normalization must NOT collapse distinct math ----

def test_normalization_preserves_operators():
    assert content_hash("what is 2+2") != content_hash("what is 2*2")
    # but case / whitespace / trailing punctuation are normalized away
    assert content_hash("Convert 10 KG to LB?") == content_hash("convert 10 kg to lb")
    assert normalize_query("  Hello,  World!! ") == "hello, world"


# ---- content + method dedup and reuse across two instances ----

def test_reuse_tool_answer_across_instances(tmp_path):
    db = tmp_path / "l9.db"
    q = "what is (9*4)-6 ?"

    a = Ledger(db, instance_id="A")
    r1 = engine.run(q, registry=_reg(), tools=default_registry(), ledger=a)
    assert r1["answer"] == "30"
    assert r1["prior"]["content_seen"] is False and r1["prior"]["reused"] is False
    a.close()

    # a different instance asks the same thing -> sees prior content and reuses it
    b = Ledger(db, instance_id="B")
    r2 = engine.run(q, registry=_reg(), tools=default_registry(), ledger=b)
    assert r2["answer"] == "30"
    assert r2["prior"]["content_seen"] is True
    assert r2["prior"]["content_prior_instance"] == "A"
    assert r2["prior"]["reused"] is True
    assert r2["answer_source"].startswith("reused:tool#")
    b.close()


def test_method_seen_even_when_content_is_new(tmp_path):
    db = tmp_path / "l9.db"
    led = Ledger(db, instance_id="A")
    engine.run("what is (9*4)-6 ?", registry=_reg(), tools=default_registry(), ledger=led)
    # new content, but same method (math_arithmetic | tool | calculator)
    r = engine.run("what is 2+2", registry=_reg(), tools=default_registry(), ledger=led)
    assert r["prior"]["content_seen"] is False     # different normalized query
    assert r["prior"]["method_seen"] is True       # method already used
    assert r["prior"]["reused"] is False
    led.close()


def test_no_false_reuse_for_distinct_math(tmp_path):
    db = tmp_path / "l9.db"
    led = Ledger(db, instance_id="A")
    r1 = engine.run("what is 2+2", registry=_reg(), tools=default_registry(), ledger=led)
    r2 = engine.run("what is 2*2", registry=_reg(), tools=default_registry(), ledger=led)
    assert r1["answer"] == "4" and r2["answer"] == "4"   # 2+2 and 2*2 both 4, coincidentally
    r3 = engine.run("what is 2+3", registry=_reg(), tools=default_registry(), ledger=led)
    assert r3["answer"] == "5" and r3["prior"]["reused"] is False
    led.close()


def test_method_hash_signature_is_stable():
    d = {"kind": "tool", "target": "calculator"}
    assert method_hash("math_arithmetic", d) == method_hash("math_arithmetic", d)
    assert method_hash("math_arithmetic", d) != method_hash("date_math", d)


# ---- SPL S7: content/method as a closed, governed class ----

def test_method_class_is_closed_two_valued():
    assert method_class({"kind": "tool"}) == "deterministic"
    assert method_class({"kind": "model"}) == "stochastic"
    assert method_class({"kind": "none"}) == "stochastic"


def test_s7_same_content_different_method_kept_distinct_and_not_reused(tmp_path):
    db = tmp_path / "l9.db"
    q = "what is 2+2"
    led = Ledger(db, instance_id="A")

    # 1) deterministic (tool) run -> answer produced, method_class deterministic
    r1 = engine.run(q, registry=_reg(), tools=default_registry(),
                    task_class="math_arithmetic", ledger=led)
    assert r1["answer"] == "4"
    assert r1["prior"]["method_class"] == "deterministic"

    # 2) SAME content, but routed as a stochastic (model) task -> must NOT reuse
    #    the deterministic answer (S7), and content is flagged as seen-under-other-method
    r2 = engine.run(q, registry=_reg(), tools=default_registry(),
                    task_class="code_audit", execute_model=False, ledger=led)
    assert r2["prior"]["content_seen"] is True          # same normalized content
    assert r2["prior"]["method_class"] == "stochastic"
    assert r2["prior"]["reused"] is False               # never reuse across the boundary
    assert r2["prior"]["content_other_method"] is True  # kept distinct per S7

    # 3) deterministic again -> reuses the deterministic prior (#1), ignoring the stochastic row
    r3 = engine.run(q, registry=_reg(), tools=default_registry(),
                    task_class="math_arithmetic", ledger=led)
    assert r3["prior"]["reused"] is True
    assert r3["answer_source"].startswith("reused:tool#")
    led.close()
