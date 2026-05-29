"""Memory Explorer — a plain view of 'open questions / conflicts / recent changes' from REAL state.

The Wild Brother (heretical role) asked: "where's the thing that shows me what matters?" This
reads state that ALREADY exists in the repo — the paper-audit findings on the DESi paper, and the
honest-failure / dual-layer probe reports — and presents them as three human buckets:

  * Conflicts        : contradictions / inconsistencies found (from the paper audit)
  * Open questions   : honestly-documented unknowns / failures (from probe honest-failure reports)
  * Recent changes   : the latest git-tracked report artifacts

No new analysis, no jargon. Deterministic given the same repo state.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[0]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_REPO / "utility_evolution" / "paper_audit"))

from glossary import say  # noqa: E402


def _conflicts_from_paper(paper: Path) -> list:
    if not paper.exists():
        return []
    try:
        import audit
        issues = audit.audit(paper.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for i in issues:
        if i.severity in ("high", "medium"):
            out.append(say(f"[{i.severity}] {i.why}") + f"  (line {i.line})")
    return out


def _open_questions(repo: Path) -> list:
    """Pull bullet lines from honest-failure reports across the repo (already-written state)."""
    qs = []
    for rpt in sorted(repo.glob("**/honest_failures*.md")) + sorted(repo.glob("**/honest_failure*.md")):
        for ln in rpt.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            if s.startswith("- ") and any(w in s.lower() for w in
                                          ("not", "cannot", "fail", "lost", "missing", "unclear", "did not")):
                qs.append(say(s[2:].strip()))
    # de-dup, keep order
    seen, out = set(), []
    for q in qs:
        k = q[:60]
        if k not in seen:
            seen.add(k)
            out.append(q)
    return out


def _recent_changes(repo: Path, limit: int = 8) -> list:
    reports = []
    for p in repo.glob("**/reports/*.md"):
        try:
            reports.append((p.stat().st_mtime, p.relative_to(repo)))
        except Exception:
            pass
    reports.sort(reverse=True)
    return [str(p) for _, p in reports[:limit]]


def build(repo: Path = _REPO) -> dict:
    paper = repo / "README.md"
    return {
        "conflicts": _conflicts_from_paper(paper),
        "open_questions": _open_questions(repo),
        "recent_changes": _recent_changes(repo),
    }


def render(state: dict) -> str:
    md = ["# DESi Memory Explorer",
          "_A plain look at what currently needs attention. No jargon, no setup._\n"]
    md += [f"## ⚠️  Conflicts found ({len(state['conflicts'])})",
           "_Places where the text contradicts itself or a reviewer would push back._\n"]
    md += [f"- {c}" for c in state["conflicts"]] or ["- (none found right now)"]
    md += ["", f"## ❓ Open questions ({len(state['open_questions'])})",
           "_Things DESi honestly does NOT resolve — known limits worth revisiting._\n"]
    md += [f"- {q}" for q in state["open_questions"][:15]] or ["- (none recorded)"]
    md += ["", f"## 🕒 Recent work ({len(state['recent_changes'])})",
           "_The latest results you can open._\n"]
    md += [f"- `{c}`" for c in state["recent_changes"]] or ["- (none yet)"]
    return "\n".join(md) + "\n"


if __name__ == "__main__":
    print(render(build()))
