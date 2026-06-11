"""Tests for the local Layer 9 ledger — append-only, hash-chained, multi-instance."""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi_router import engine  # noqa: E402
from desi_router.ledger import Ledger  # noqa: E402
from desi_router.providers import load_config  # noqa: E402
from desi_router.tool_registry import default_registry  # noqa: E402

CONFIG = REPO_ROOT / "desi_router" / "config.example.json"


def test_record_read_and_chain(tmp_path):
    led = Ledger(tmp_path / "l9.db", instance_id="t")
    a = led.record("route", {"task_class": "math_arithmetic", "q": "2+2"}, decision_hash="aa")
    b = led.record("route", {"task_class": "date_math"}, decision_hash="bb")
    assert a["seq"] == 1 and b["seq"] == 2
    rows = led.all()
    assert [r["seq"] for r in rows] == [1, 2]
    assert rows[1]["prev_chain_hash"] == rows[0]["chain_hash"]
    assert led.verify_chain() is True
    assert led.by_decision_hash("bb")[0]["seq"] == 2
    led.close()


def test_tamper_breaks_chain(tmp_path):
    db = tmp_path / "l9.db"
    led = Ledger(db, instance_id="t")
    led.record("route", {"task_class": "x"}, decision_hash="aa")
    led.record("route", {"task_class": "y"}, decision_hash="bb")
    assert led.verify_chain() is True
    # edit a past payload directly -> chain must no longer verify
    led._con.execute("UPDATE events SET payload=? WHERE seq=1", ('{"task_class":"HACKED"}',))
    assert led.verify_chain() is False
    led.close()


def test_engine_records_to_ledger(tmp_path):
    led = Ledger(tmp_path / "l9.db", instance_id="eng")
    out = engine.run("what is (9*4)-6 ?", registry=load_config(CONFIG),
                     tools=default_registry(), ledger=led)
    assert "ledger" in out and out["ledger"]["seq"] == 1
    stored = led.all()[0]
    assert stored["kind"] == "route"
    assert stored["decision_hash"] == out["audit"]["decision_hash"]
    led.close()


def test_concurrent_multi_instance(tmp_path):
    """Several processes (= several local DESi instances) append at once."""
    db = tmp_path / "l9.db"
    code = (
        "import sys;from desi_router.ledger import Ledger;"
        "p,iid,m=sys.argv[1],sys.argv[2],int(sys.argv[3]);"
        "l=Ledger(p,instance_id=iid);"
        "[l.record('route',{'i':i,'task_class':'math_arithmetic'}) for i in range(m)];"
        "l.close()"
    )
    n, m = 4, 25
    procs = [
        subprocess.Popen([sys.executable, "-c", code, str(db), f"inst{k}", str(m)],
                         cwd=str(REPO_ROOT))
        for k in range(n)
    ]
    for p in procs:
        assert p.wait() == 0

    led = Ledger(db, instance_id="checker")
    stats = led.stats()
    assert stats["count"] == n * m
    assert len(stats["instances"]) == n            # every instance landed
    assert led.verify_chain() is True              # chain intact despite concurrency
    seqs = [e["seq"] for e in led.all()]
    assert seqs == list(range(1, n * m + 1))       # contiguous, no gaps/dups
    led.close()


def test_all_limit_zero_returns_no_rows(tmp_path):
    led = Ledger(tmp_path / "l9.db", instance_id="t")
    led.record("route", {"task_class": "x"})
    assert led.all(limit=0) == []                  # 0 is a limit, not "no limit"
    assert len(led.all(limit=1)) == 1
    assert len(led.all()) == 1
    led.close()


def test_record_survives_held_write_lock(tmp_path):
    """A second writer holding the lock past busy_timeout must lead to a retry,
    never to an uncaught 'cannot rollback - no transaction is active'."""
    db = tmp_path / "l9.db"
    led = Ledger(db, instance_id="b", busy_timeout_ms=100)
    blocker = sqlite3.connect(str(db), isolation_level=None, check_same_thread=False)
    blocker.execute("BEGIN IMMEDIATE")
    t = threading.Timer(0.5, blocker.execute, args=("COMMIT",))
    t.start()
    entry = led.record("route", {"task_class": "x"})   # retries until the lock clears
    assert entry["seq"] == 1
    t.join()
    blocker.close()
    led.close()


def test_verify_chain_incremental(tmp_path):
    led = Ledger(tmp_path / "l9.db", instance_id="t")
    led.record("route", {"task_class": "x"})
    ok, seq, head = led.verify_chain_from()
    assert ok is True and seq == 1
    led.record("route", {"task_class": "y"})
    ok2, seq2, _head2 = led.verify_chain_from(seq, head)   # verifies only row 2
    assert ok2 is True and seq2 == 2
    # tamper -> incremental verification from the verified prefix catches it
    led._con.execute("UPDATE events SET payload=? WHERE seq=2", ('{"task_class":"HACKED"}',))
    ok3, _, _ = led.verify_chain_from(seq, head)
    assert ok3 is False
    led.close()
