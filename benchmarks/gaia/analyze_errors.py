#!/usr/bin/env python3
"""Per-task error analysis for a GAIA run.

Reads a submission JSONL and the gold split, classifies every task into one
rough failure class, prints a per-task table, and writes a Markdown report.

Classes (one primary label per task, assigned in this priority order):
  correct, attachment_skipped, backend_error, reasoning_truncated,
  needs_web_search_or_tools, empty_or_unknown, wrong_answer, unknown_failure

The HF token is read **only** from the environment (gated dataset access). No
secrets are read, logged, or written.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_validation import normalize  # same lenient exact-match

DATASET_ID = "gaia-benchmark/GAIA"
_OUT = Path(__file__).resolve().parent / "outputs"
DEFAULT_SUBMISSION = _OUT / "submission.validation.deepseek-v4.textonly.limit10.jsonl"
DEFAULT_REPORT = _OUT / "error_report.deepseek-v4.textonly.limit10.md"

# Markers in the question that suggest the task needs external lookup or tools
# (web search, a database, a specific source) rather than self-contained reasoning.
_EXTERNAL_MARKERS = (
    "according to", "arxiv", "http", "www.", "website", "wikipedia", "usgs",
    "published", "journal", "the paper", "article", "database", "youtube",
    "as of", "latest", " current ", "encyclopedia", "census", "imdb", "github",
    "google", "browse", "url", "doi", "pubmed", "openreview", "discography",
    "nature ", "submitted to", "magazine", "catalog",
)

CLASSES = (
    "correct", "attachment_skipped", "backend_error", "reasoning_truncated",
    "needs_web_search_or_tools", "empty_or_unknown", "wrong_answer",
    "unknown_failure",
)


def _is_empty(answer: object) -> bool:
    return str(answer).strip() == ""


def _is_unknown(answer: object) -> bool:
    return str(answer).strip().upper() == "UNKNOWN"


def _needs_external(question: str) -> bool:
    q = f" {question.lower()} "
    return any(m in q for m in _EXTERNAL_MARKERS)


def _finish_reason(meta: dict) -> str | None:
    audit = meta.get("audit") or {}
    return meta.get("finish_reason") or audit.get("finish_reason")


def _truncation_hint(answer: str, error: str | None, meta: dict) -> str:
    fr = _finish_reason(meta)
    if fr == "length":
        return "finish_reason=length (truncated)"
    if _is_empty(answer) and not (error or "").strip():
        return "likely truncated (empty content, no backend error)"
    return "n/a"


def classify(answer: str, meta: dict, error: str | None,
             question: str, correct: bool) -> str:
    status = meta.get("attachment_status")
    err = error or ""
    if status == "skipped" or "requires an attachment" in err:
        return "attachment_skipped"
    if any(s in err for s in ("call failed", "ModuleNotFoundError", "http_",
                              "HTTPError", "URLError", "timeout")):
        return "backend_error"
    if correct:
        return "correct"
    if _is_empty(answer):
        return "reasoning_truncated" if not err.strip() else "unknown_failure"
    # Non-empty but wrong, or an explicit UNKNOWN.
    if _needs_external(question):
        return "needs_web_search_or_tools"
    if _is_unknown(answer):
        return "empty_or_unknown"
    return "wrong_answer"


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-task GAIA error analysis.")
    parser.add_argument("--submission", type=Path, default=DEFAULT_SUBMISSION)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", default="2023_all")
    parser.add_argument("--split", default="validation")
    args = parser.parse_args()

    if not args.submission.exists():
        print(f"Submission not found: {args.submission}", file=sys.stderr)
        return 1

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    try:
        from datasets import load_dataset
    except ModuleNotFoundError:
        print("Missing dependency. Install with: pip install datasets", file=sys.stderr)
        return 1
    try:
        ds = load_dataset(DATASET_ID, args.config, split=args.split, token=token)
    except Exception as exc:
        print(f"Failed to load {DATASET_ID} [{args.config}/{args.split}]: {exc}",
              file=sys.stderr)
        return 1
    gold = {
        row["task_id"]: {
            "answer": row.get("Final answer", ""),
            "level": row.get("Level", ""),
            "has_attachment": bool((row.get("file_name") or "").strip()),
        }
        for row in ds
    }

    rows = []
    counts = Counter()
    per_level = {}  # level -> [correct, total]
    total = correct_n = without_attach = correct_no_attach = unknown_empty = 0

    for line in args.submission.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        meta = entry.get("desi_metadata", {})
        task_id = entry.get("task_id", "")
        g = gold.get(task_id, {"answer": "", "level": meta.get("level", "?"),
                               "has_attachment": meta.get("requires_attachment", False)})
        answer = entry.get("model_answer", "")
        error = meta.get("error")
        question = (meta.get("audit") or {}).get("question", "")
        is_unknown_empty = _is_empty(answer) or _is_unknown(answer)
        is_correct = (not is_unknown_empty
                      and normalize(answer) == normalize(g["answer"]))
        klass = classify(answer, meta, error, question, is_correct)

        counts[klass] += 1
        total += 1
        correct_n += int(is_correct)
        lvl = g["level"]
        per_level.setdefault(lvl, [0, 0])
        per_level[lvl][1] += 1
        per_level[lvl][0] += int(is_correct)
        if is_unknown_empty:
            unknown_empty += 1
        if not g["has_attachment"]:
            without_attach += 1
            correct_no_attach += int(is_correct)

        rows.append({
            "task_id": task_id,
            "level": g["level"],
            "question": question,
            "gold": g["answer"],
            "answer": answer,
            "correct": is_correct,
            "empty_or_unknown": is_unknown_empty,
            "requires_attachment": meta.get("requires_attachment", g["has_attachment"]),
            "solver": meta.get("solver", ""),
            "backend": meta.get("backend", ""),
            "model": meta.get("model", ""),
            "error": error or "",
            "finish_reason": _finish_reason(meta) or "n/a (not captured)",
            "truncation_hint": _truncation_hint(answer, error, meta),
            "class": klass,
        })

    def pct(c: int, t: int) -> str:
        return f"{100.0 * c / t:.1f}%" if t else "n/a"

    def short(s: str, n: int = 90) -> str:
        s = " ".join(str(s).split())
        return s if len(s) <= n else s[: n - 1] + "…"

    # ---- console output -------------------------------------------------- #
    print(f"Submission: {args.submission}")
    print(f"Gold:       {DATASET_ID} [{args.config}/{args.split}]\n")
    for r in rows:
        print(f"[{r['task_id'][:8]}] L{r['level']} {r['class']}")
        print(f"    Q: {short(r['question'], 80)}")
        print(f"    gold={r['gold']!r}  model={r['answer'][:40]!r}  "
              f"correct={r['correct']}  empty/UNKNOWN={r['empty_or_unknown']}")
        print(f"    solver={r['solver']} backend={r['backend']} model={r['model']} "
              f"req_attach={r['requires_attachment']}")
        print(f"    finish_reason={r['finish_reason']}  trunc={r['truncation_hint']}")
        if r["error"]:
            print(f"    error: {short(r['error'], 100)}")
    print()
    print(f"Accuracy overall   : {correct_n}/{total} = {pct(correct_n, total)}")
    print(f"Accuracy text-only : {correct_no_attach}/{without_attach} = "
          f"{pct(correct_no_attach, without_attach)}")
    print(f"UNKNOWN/empty      : {unknown_empty}")
    print("By class: " + ", ".join(f"{k}={counts[k]}" for k in CLASSES if counts[k]))

    # ---- markdown report ------------------------------------------------- #
    md = []
    md.append(f"# GAIA error analysis — {args.submission.name}\n")
    md.append(f"- Dataset: `{DATASET_ID}` [{args.config}/{args.split}]")
    md.append(f"- Tasks scored: **{total}**")
    md.append(f"- Accuracy overall: **{correct_n}/{total} = {pct(correct_n, total)}**")
    md.append(f"- Accuracy text-only: **{correct_no_attach}/{without_attach} = "
              f"{pct(correct_no_attach, without_attach)}**")
    md.append(f"- UNKNOWN/empty answers: **{unknown_empty}**")
    md.append(f"- Suspected reasoning-truncation: **{counts['reasoning_truncated']}**")
    md.append(f"- Suspected web/search/tools needed: "
              f"**{counts['needs_web_search_or_tools']}**\n")

    md.append("## By error class\n")
    md.append("| class | count |")
    md.append("| --- | --- |")
    for k in CLASSES:
        md.append(f"| {k} | {counts[k]} |")
    md.append("")

    md.append("## By level\n")
    md.append("| level | correct | total | accuracy |")
    md.append("| --- | --- | --- | --- |")
    for lvl in sorted(per_level, key=lambda x: str(x)):
        c, t = per_level[lvl]
        md.append(f"| {lvl} | {c} | {t} | {pct(c, t)} |")
    md.append("")

    md.append("## Per-task\n")
    md.append("| task_id | L | class | correct | empty/UNK | req_att | model_answer | gold | finish_reason | question |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        md.append("| {tid} | {lvl} | {cls} | {ok} | {eu} | {ra} | {ans} | {gold} | {fr} | {q} |".format(
            tid=r["task_id"][:8], lvl=r["level"], cls=r["class"],
            ok="✓" if r["correct"] else "✗",
            eu="yes" if r["empty_or_unknown"] else "no",
            ra="yes" if r["requires_attachment"] else "no",
            ans=short(r["answer"].replace("|", "\\|"), 30) or "(empty)",
            gold=short(str(r["gold"]).replace("|", "\\|"), 25),
            fr=r["finish_reason"],
            q=short(r["question"].replace("|", "\\|"), 70),
        ))
    md.append("")
    md.append("> Classes are heuristic. `reasoning_truncated` is inferred from an "
              "empty answer with no backend error (the reasoning model emitted no "
              "content); `needs_web_search_or_tools` is inferred from external-lookup "
              "markers in the question. `finish_reason` is only shown when the run "
              "captured it.")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nWrote report to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
