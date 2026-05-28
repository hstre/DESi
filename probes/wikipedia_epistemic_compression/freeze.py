"""Freeze a reproducible, non-curated random sample of Wikipedia articles.

Selection = `random.Random(SEED).sample(sorted(featured_pool), N)`. The pool (mainspace
Featured Articles) is pinned by size + sha256; the resolved titles/pageids, seed, pool
hash and timestamp are written to frozen_article_set.json and the article texts are cached.
Run ONCE (live); thereafter the committed frozen set + cache replay deterministically.

    python probes/wikipedia_epistemic_compression/freeze.py
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from fetch import _now, featured_pool, get_article  # noqa: E402

SEED = 20260528           # documented seed (YYYYMMDD of the freeze date); not chosen by result
N = 10
FROZEN = _HERE / "data" / "frozen_article_set.json"


def freeze(live: bool = True) -> dict:
    pool = featured_pool()
    pool_sha = hashlib.sha256("\n".join(pool).encode("utf-8")).hexdigest()
    selected_titles = sorted(random.Random(SEED).sample(pool, N))
    articles = [get_article(t, live=live) for t in selected_titles]
    frozen = {
        "seed": SEED,
        "selection_rule": "random.Random(SEED).sample(sorted(pool), N)",
        "pool_source": "Category:Featured articles (namespace 0)",
        "pool_size": len(pool),
        "pool_sha256": pool_sha,
        "n": N,
        "frozen_at": _now(),
        "selected": [{"requested_title": t, "title": a["title"], "pageid": a["pageid"],
                      "fetched_at": a.get("fetched_at")}
                     for t, a in zip(selected_titles, articles)],
    }
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    FROZEN.write_text(json.dumps(frozen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return frozen


def load_frozen() -> dict:
    return json.loads(FROZEN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    fr = freeze(live=True)
    print(f"frozen {fr['n']} articles (seed={fr['seed']}, pool={fr['pool_size']}):")
    for s in fr["selected"]:
        print(f"  {s['pageid']}  {s['title']}")
