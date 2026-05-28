"""Minimal, polite MediaWiki client with on-disk caching (no embeddings, no retrieval engine).

Fetches plain article text (with section headers) and wikitext (for citation counting),
caching each article under data/cache/ keyed by title hash. After one live run the cache is
committed, so the whole probe replays deterministically OFFLINE from cache.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
CACHE = _HERE / "data" / "cache"
API = "https://en.wikipedia.org/w/api.php"
UA = "DESi-epistemic-probe/0.1 (research; contact hstrex@googlemail.com)"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(params: dict, timeout: int = 30, retries: int = 4) -> dict:
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:  # noqa: BLE001 - network errors retried with backoff
            last = e
            time.sleep(2 ** i)
    raise RuntimeError(f"Wikipedia API failed after {retries} tries: {last}")


def featured_pool() -> list:
    """Sorted, de-duplicated list of mainspace Featured Articles (the random pool)."""
    titles, cont = [], {}
    while True:
        d = _get({"action": "query", "list": "categorymembers",
                  "cmtitle": "Category:Featured articles", "cmnamespace": 0,
                  "cmlimit": "500", **cont})
        titles += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" in d:
            cont = d["continue"]
            time.sleep(0.2)
        else:
            break
    return sorted(set(titles))


def _fetch_live(title: str) -> dict:
    d = _get({"action": "query", "prop": "extracts", "explaintext": 1,
              "exsectionformat": "wiki", "redirects": 1, "titles": title})
    page = next(iter(d["query"]["pages"].values()))
    w = _get({"action": "query", "prop": "revisions", "rvprop": "content",
              "rvslots": "main", "redirects": 1, "titles": title})
    wpage = next(iter(w["query"]["pages"].values()))
    wikitext = ""
    try:
        wikitext = wpage["revisions"][0]["slots"]["main"]["*"]
    except Exception:  # noqa: BLE001
        wikitext = ""
    return {"requested_title": title, "title": page.get("title", title),
            "pageid": page.get("pageid"), "plaintext": page.get("extract", "") or "",
            "wikitext": wikitext, "fetched_at": _now()}


def _cache_path(title: str) -> Path:
    key = hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]
    return CACHE / f"{key}.json"


def get_article(title: str, live: bool = True) -> dict:
    """Return the cached article, fetching + caching it live on a miss."""
    fp = _cache_path(title)
    if fp.exists():
        return json.loads(fp.read_text(encoding="utf-8"))
    if not live:
        raise FileNotFoundError(f"no cached article for {title!r} (live=False)")
    CACHE.mkdir(parents=True, exist_ok=True)
    art = _fetch_live(title)
    time.sleep(0.3)
    fp.write_text(json.dumps(art, ensure_ascii=False), encoding="utf-8")
    return art
