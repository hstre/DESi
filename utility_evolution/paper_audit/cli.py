"""One-command CLI: audit any markdown paper for epistemic/structural defects.

    python -m utility_evolution.paper_audit.cli path/to/paper.md
    python utility_evolution/paper_audit/cli.py path/to/paper.md

Deterministic and replay-hashed (re-running on the same file yields the same report + hash).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from desi.core.replay_kernel import replay_hash  # noqa: E402

from audit import audit  # noqa: E402


def format_report(issues, path: str) -> str:
    counts = {}
    for i in issues:
        counts[i.severity] = counts.get(i.severity, 0) + 1
    head = [f"# Paper audit — {path}",
            f"{len(issues)} issue(s): " + ", ".join(f"{k} {counts[k]}" for k in sorted(counts)) or "none",
            ""]
    body = []
    for n, i in enumerate(issues, start=1):
        body += [f"## {n}. [{i.severity.upper()}] {i.check} (line {i.line})",
                 f"- where: {i.quote}", f"- why: {i.why}", f"- fix: {i.fix}", ""]
    if not issues:
        body = ["No deterministic issues found (this does NOT mean the paper is sound — "
                "semantic problems are out of scope; see the tool's honest-failure notes)."]
    return "\n".join(head + body)


def run(path: str) -> int:
    text = Path(path).read_text(encoding="utf-8")
    issues = audit(text)
    report = format_report(issues, path)
    rh = replay_hash([(i.severity, i.check, i.line, i.quote) for i in issues])
    print(report)
    print(f"\nreplay_hash: {rh[:16]}  ({len(issues)} issues)")
    return len(issues)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: cli.py <markdown-file>")
        sys.exit(2)
    run(sys.argv[1])
