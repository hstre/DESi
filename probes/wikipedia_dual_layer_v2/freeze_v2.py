"""Freeze a NEW held-out random sample for v2 generalization testing.

Same selection rule and pool as v1, but a different documented seed (NEW_SEED) and a
SEPARATE cache (v2/data/cache) so the v1 probe's frozen set + cache are not touched.
Run ONCE live; thereafter replays offline from the committed cache.

    python probes/wikipedia_dual_layer_v2/freeze_v2.py
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "wikipedia_epistemic_compression"))

from fetch import _fetch_live, _now, featured_pool  # noqa: E402  (reused live fetch)
from preregistration import N, NEW_SEED  # noqa: E402

V2_CACHE = _HERE / "data" / "cache"
FROZEN = _HERE / "data" / "frozen_article_set_v2.json"


def get_article_v2(title: str, live: bool = True) -> dict:
    fp = V2_CACHE / (hashlib.sha256(title.encode("utf-8")).hexdigest()[:16] + ".json")
    if fp.exists():
        return json.loads(fp.read_text(encoding="utf-8"))
    if not live:
        raise FileNotFoundError(f"no cached v2 article for {title!r}")
    V2_CACHE.mkdir(parents=True, exist_ok=True)
    art = _fetch_live(title)
    time.sleep(0.3)
    fp.write_text(json.dumps(art, ensure_ascii=False), encoding="utf-8")
    return art


def freeze(live: bool = True) -> dict:
    pool = featured_pool()
    pool_sha = hashlib.sha256("\n".join(pool).encode("utf-8")).hexdigest()
    titles = sorted(random.Random(NEW_SEED).sample(pool, N))
    arts = [get_article_v2(t, live=live) for t in titles]
    frozen = {
        "seed": NEW_SEED, "selection_rule": "random.Random(NEW_SEED).sample(sorted(pool), N)",
        "pool_source": "Category:Featured articles (namespace 0)", "pool_size": len(pool),
        "pool_sha256": pool_sha, "n": N, "frozen_at": _now(), "held_out_for": "v2 generalization",
        "selected": [{"requested_title": t, "title": a["title"], "pageid": a["pageid"],
                      "fetched_at": a.get("fetched_at")} for t, a in zip(titles, arts)],
    }
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    FROZEN.write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return frozen


def load_frozen() -> dict:
    return json.loads(FROZEN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    fr = freeze(live=True)
    print(f"frozen NEW {fr['n']} articles (seed={fr['seed']}, pool={fr['pool_size']}):")
    for s in fr["selected"]:
        print(f"  {s['pageid']}  {s['title']}")
