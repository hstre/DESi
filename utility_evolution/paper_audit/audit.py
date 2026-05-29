"""Deterministic markdown-paper epistemic auditor (offline, no embeddings, no LLM).

Operationalizes the manual Reviewer-Port audit into reusable checks. Each check is a pure
function of the document text and returns Issue records (severity, line, quote, why, fix).
This is the BUILT survivor of the utility-evolution screening: it saves a reviewer time (Q5),
makes review transparent and reproducible (Q7), and is reusable on any markdown paper.

Honest scope: these catch DETERMINISTIC / structural defects (numeric range mismatches,
near-duplicate paragraphs, table-order errors, traceability-boilerplate contradictions,
overclaim terms). They do NOT catch subtle semantic problems (e.g. a self-audit that claims
fixes it never made) — see the honest-failure report.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_STOP = frozenset((
    "the a an of to in on and or is are was were be been being that this these those it its as at "
    "by for with from has have had do does did but if then than so such into out up down over under "
    "about their they them we you i which who not no only any all per also more most some can").split())

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# topic keywords that should carry a consistent numeric range across a paper
TOPIC_KEYWORDS = ("compression", "reduction", "node", "recoverability", "precision", "recall",
                  "accuracy", "savings", "node_reduction", "search")

RISK_TERMS = ("unknown unknowns", "breakthrough", "revolutionary", "world model", "truth engine",
              "human-level", "state of the art", "state-of-the-art", "paradigm shift",
              "by construction", "trivially", "obviously", "guarantee", "proves that")


@dataclass(frozen=True)
class Issue:
    severity: str
    check: str
    line: int
    quote: str
    why: str
    fix: str


def _content(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", text.lower()) if t not in _STOP and len(t) > 2}


def _lines(text: str):
    return text.split("\n")


def _paragraphs(text: str):
    """Return [(start_line, text)] for blank-line-separated blocks."""
    out, buf, start = [], [], 1
    for i, ln in enumerate(text.split("\n"), start=1):
        if ln.strip() == "":
            if buf:
                out.append((start, " ".join(buf)))
            buf, start = [], i + 1
        else:
            if not buf:
                start = i
            buf.append(ln.strip())
    if buf:
        out.append((start, " ".join(buf)))
    return out


def _snippet(s: str, n: int = 90) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n]


def check_numeric_consistency(text: str) -> list:
    """Flag percentage RANGES for the same topic keyword that disagree across the paper."""
    issues, by_topic = [], {}
    for i, ln in enumerate(_lines(text), start=1):
        low = ln.lower()
        topic = next((k for k in TOPIC_KEYWORDS if k in low), None)
        if topic is None:
            continue
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*[–\-]\s*(\d+(?:\.\d+)?)\s*%", ln):
            rng = (float(m.group(1)), float(m.group(2)))
            by_topic.setdefault(topic, []).append((rng, i, _snippet(ln)))
    for topic, hits in by_topic.items():
        distinct = {h[0] for h in hits}
        if len(distinct) > 1:
            locs = ", ".join(f"L{h[1]}:{h[0][0]:g}–{h[0][1]:g}%" for h in hits)
            issues.append(Issue("high", "numeric_consistency", hits[0][1],
                                f"'{topic}' ranges: {locs}",
                                f"the same topic '{topic}' is given {len(distinct)} different "
                                "percentage ranges across the paper",
                                "pick one canonical range and use it everywhere (abstract/body/conclusion)"))
    return issues


def check_duplicate_paragraphs(text: str, thresh: float = 0.6, min_tokens: int = 12) -> list:
    issues = []
    paras = [(ln, p, _content(p)) for ln, p in _paragraphs(text)]
    paras = [(ln, p, c) for ln, p, c in paras if len(c) >= min_tokens]
    for a in range(len(paras)):
        for b in range(a + 1, len(paras)):
            ca, cb = paras[a][2], paras[b][2]
            jac = len(ca & cb) / len(ca | cb) if (ca | cb) else 0.0
            if jac >= thresh:
                issues.append(Issue("medium", "duplicate_paragraphs", paras[b][0],
                                    f"L{paras[a][0]} ≈ L{paras[b][0]} (Jaccard {round(jac,2)}): "
                                    f"\"{_snippet(paras[b][1], 70)}\"",
                                    "near-duplicate paragraph content (reviewers flag redundancy)",
                                    "state the passage once and cross-reference"))
    return issues


def check_structure_tables(text: str) -> list:
    """Flag Table references that appear out of numeric order (e.g. Table 2 before Table 1)."""
    issues, seen = [], []
    for i, ln in enumerate(_lines(text), start=1):
        for m in re.finditer(r"\bTable\s+(\d+)\b", ln):
            seen.append((int(m.group(1)), i, _snippet(ln)))
    first_intro = {}
    for num, ln, snip in seen:
        first_intro.setdefault(num, (ln, snip))
    intro_order = sorted(first_intro.items(), key=lambda kv: kv[1][0])  # by first-appearance line
    nums_in_order = [num for num, _ in intro_order]
    if nums_in_order != sorted(nums_in_order):
        issues.append(Issue("medium", "structure_tables", intro_order[0][1][0],
                            f"Table first-appearance order is {nums_in_order}",
                            "tables are introduced out of numeric order (e.g. Table 2 before Table 1)",
                            "renumber tables in order of first reference"))
    return issues


def check_traceability(text: str) -> list:
    low = text.lower()
    blanket = re.search(r"all (numeric(?:al)?) claims[^.]*?(deriv|traceab)", low)
    admit = re.search(r"(not (?:directly )?traceab|rather than .{0,40}artifact|companion .{0,20}paper)", low)
    issues = []
    if blanket and admit:
        bl = text[:blanket.start()].count("\n") + 1
        ad = text[:admit.start()].count("\n") + 1
        issues.append(Issue("high", "traceability", bl,
                            f"blanket traceability claim (L{bl}) vs non-traceability admission (L{ad})",
                            "a global 'all claims are artifact-traceable' statement coexists with an "
                            "admission that some claims are not traceable to repo artifacts",
                            "qualify the blanket claim to exclude the admitted exceptions"))
    return issues


def check_overclaim_terms(text: str) -> list:
    issues = []
    for i, ln in enumerate(_lines(text), start=1):
        low = ln.lower()
        for term in RISK_TERMS:
            if term in low:
                issues.append(Issue("low", "overclaim_terms", i, f"'{term}' — \"{_snippet(ln, 70)}\"",
                                    f"reviewer-risk / overclaim phrase '{term}'",
                                    "remove or qualify; avoid absolute / hype language"))
    # universal "all N ... achieved/passed" claims are easy reviewer targets
    for i, ln in enumerate(_lines(text), start=1):
        if re.search(r"\ball\s+\d+\s+\w+.*\b(achiev|passed|reach|succeed)", ln.lower()):
            issues.append(Issue("medium", "overclaim_terms", i,
                                f"universal claim — \"{_snippet(ln, 80)}\"",
                                "a falsifiable 'all N ... achieved' claim invites a single-counterexample refutation",
                                "verify against the source table; soften if any exception exists"))
    return issues


CHECKS = (check_numeric_consistency, check_duplicate_paragraphs, check_structure_tables,
          check_traceability, check_overclaim_terms)


def audit(text: str) -> list:
    issues = []
    for chk in CHECKS:
        issues.extend(chk(text))
    issues.sort(key=lambda x: (SEVERITY_ORDER.get(x.severity, 9), x.check, x.line))
    return issues
