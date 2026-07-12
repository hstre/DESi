"""Europe PMC access: search the PMC OA subset and fetch JATS full-text XML (stdlib).

No API key required. We restrict to open-access, full-text-in-EPMC, human studies, and
exclude non-empirical article types at the query level (the JATS parser re-checks
``article-type`` as the authoritative filter).
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request

_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

# Query-level eligibility: OA full text, in EPMC, PMC source, human studies; exclude
# reviews / editorials / comments / corrections / protocols at the search layer.
_EXCLUDE_TYPES = ('review', 'review-article', 'editorial', 'comment', 'correction',
                  'letter', 'case-report', 'protocol')
BASE_ELIGIBILITY = (
    'OPEN_ACCESS:y AND IN_EPMC:y AND HAS_FT:y AND SRC:PMC AND MESH:"Humans"'
    ' AND ' + ' AND '.join(f'NOT PUB_TYPE:"{t}"' for t in _EXCLUDE_TYPES)
)


def _get(url: str, timeout: int = 60, retries: int = 4) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "desi-extval/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - network resilience
            last = e
            time.sleep(2 ** i)
    raise RuntimeError(f"GET failed after {retries}: {url} ({last})")


def search(phrase_query: str, page_size: int = 25, cursor: str = "*") -> dict:
    """Search PMC OA for `BASE_ELIGIBILITY AND (phrase_query)`; returns one page."""
    q = f"({BASE_ELIGIBILITY}) AND ({phrase_query})"
    params = urllib.parse.urlencode({
        "query": q, "resultType": "core", "format": "json",
        "pageSize": page_size, "cursorMark": cursor,
    })
    data = json.loads(_get(f"{_SEARCH}?{params}"))
    return {
        "hit_count": data.get("hitCount", 0),
        "next_cursor": data.get("nextCursorMark"),
        "results": [{
            "pmcid": r.get("pmcid"),
            "pmid": r.get("pmid"),
            "title": r.get("title", ""),
            "journal": (r.get("journalInfo", {}) or {}).get("journal", {}).get("title", ""),
            "pub_types": (r.get("pubTypeList", {}) or {}).get("pubType", []),
            "year": r.get("pubYear"),
        } for r in data.get("resultList", {}).get("result", []) if r.get("pmcid")],
    }


def fetch_fulltext_xml(pmcid: str) -> str:
    """Fetch JATS full-text XML for a PMCID (e.g. 'PMC1234567')."""
    return _get(_FULLTEXT.format(pmcid=pmcid)).decode("utf-8", errors="replace")


__all__ = ["BASE_ELIGIBILITY", "search", "fetch_fulltext_xml"]
