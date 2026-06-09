"""Tests for the local Layer 9 ledger — append-only, hash-chained, multi-instance."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from desi import engine  # noqa: E402
from desi.ledger import Ledger  # noqa: E402
from desi.providers import load_config  # noqa: E402
from desi.tool_registry import default_registry  # noqa: E402

CONFIG = REPO_ROOT / "desi" / "config.example.json"


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
        "import sys;from desi.ledger import Ledger;"
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
