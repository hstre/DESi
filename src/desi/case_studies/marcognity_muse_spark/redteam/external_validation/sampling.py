"""Two-stage stratified sampling over the PMC OA subset (empirical human studies).

Eligibility (research articles only; empirical/quantitative; exclude review/editorial/
protocol/qualitative) is enforced here on the parsed JATS ``article-type`` and title,
on top of the query-level filters in ``europepmc``. Stage 2 (blind) excludes every
PMCID used in Stage 1 (pilot), so the frozen blind test is disjoint.
"""
from __future__ import annotations

from . import candidates, europepmc, jats

# seed phrases spanning the four strata, so the document pool is not only 'p <'
SEED_PHRASES = (
    '"statistically significant"', '"confidence interval"', '"effect size"',
    '"clinically significant"', '"odds ratio"', '"minimal important difference"',
    '"clinically meaningful"', '"no significant difference"',
)
_TITLE_EXCLUDE = ("systematic review", "meta-analysis", "meta analysis", "scoping review",
                  "narrative review", "literature review", "study protocol", "protocol for",
                  "qualitative", "review of", "rapid review", "umbrella review")


def is_eligible(doc: jats.Document) -> tuple[bool, str]:
    if doc.article_type not in ("research-article", "research article", ""):
        return False, f"article_type:{doc.article_type}"
    t = (doc.title or "").lower()
    if any(b in t for b in _TITLE_EXCLUDE):
        return False, "title_excluded"
    present: set[str] = set()
    for para in doc.paragraphs:
        for s in para.sentences:
            present |= {n for n, rx in candidates.STRATA.items() if rx.search(s)}
    if not ({"p_value", "conf_int", "effect_size"} & present):
        return False, "no_quantitative_markers"
    return True, "ok"


def build_stage(target_docs: int, target_claims: int, max_per_doc: int, rng,
                exclude_pmcids: set[str] | None = None, page_size: int = 25,
                fetch=europepmc.fetch_fulltext_xml, log=lambda *_: None) -> dict:
    """Collect eligible docs (round-robin over seed phrases), emit stratified claims."""
    exclude = set(exclude_pmcids or set())
    cursors = {p: "*" for p in SEED_PHRASES}
    used: list[str] = []
    claims: list[dict] = []
    seen: set[str] = set(exclude)
    cid = 0
    rounds = 0
    while len(used) < target_docs and len(claims) < target_claims and rounds < 200:
        rounds += 1
        for phrase in SEED_PHRASES:
            if len(used) >= target_docs or len(claims) >= target_claims:
                break
            page = europepmc.search(phrase, page_size=page_size, cursor=cursors[phrase])
            cursors[phrase] = page["next_cursor"] or cursors[phrase]
            for meta in page["results"]:
                pmcid = meta["pmcid"]
                if pmcid in seen:
                    continue
                seen.add(pmcid)
                try:
                    doc = jats.parse(fetch(pmcid), pmcid)
                except Exception as e:  # noqa: BLE001
                    log(f"skip {pmcid}: parse {e}")
                    continue
                ok, why = is_eligible(doc)
                if not ok:
                    log(f"skip {pmcid}: {why}")
                    continue
                cands = candidates.select_stratified(
                    candidates.find_candidates(doc), max_per_doc, rng)
                if not cands:
                    continue
                for c in cands:
                    cid += 1
                    c["claim_id"] = f"C{cid:04d}"
                used.append(pmcid)
                claims.extend(cands)
                log(f"doc {pmcid}: +{len(cands)} claims ({len(claims)} total, "
                    f"{len(used)} docs)")
                if len(used) >= target_docs or len(claims) >= target_claims:
                    break
    return {"claims": claims[:target_claims], "pmcids": used}


__all__ = ["SEED_PHRASES", "is_eligible", "build_stage"]
