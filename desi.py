#!/usr/bin/env python3
"""DESi — one command, plain language. Your starting point.

    python desi.py                 # DESi Home: what it does + your first step (30-second overview)
    python desi.py home
    python desi.py check FILE      # check a paper/document for reviewer-level problems
    python desi.py decide FILE     # compare options (JSON) and record a decision + trade-offs
    python desi.py memory          # see conflicts / open questions / recent work, in plain language
    python desi.py wizard          # answer plain questions; get the exact command to run

No DESi-internal terms required. This is a thin, user-facing entry point over the existing
tools (utility_evolution.paper_audit, .decision_record) and the human_interface package.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "src"))
sys.path.insert(0, str(_HERE / "human_interface"))
sys.path.insert(0, str(_HERE / "utility_evolution" / "paper_audit"))
sys.path.insert(0, str(_HERE / "utility_evolution" / "decision_record"))

HOME = """\
============================================================
  DESi — a quality check & memory helper for your work
============================================================

WHAT IT DOES (in plain words)
  • Checks a paper or document for the problems a reviewer
    would catch: inconsistent numbers, repeated text,
    contradictions, over-strong claims.
  • Helps you compare options and records WHY you chose one,
    including the trade-off you accepted.
  • Shows you what currently needs attention: conflicts,
    open questions, and recent work.

WHAT YOU CAN DO RIGHT NOW
  python desi.py check  <your-file.md>     -> ranked list of issues
  python desi.py decide <options.json>     -> recommendation + trade-off
  python desi.py memory                    -> what needs attention
  python desi.py wizard                    -> guided, asks plain questions

WHERE TO START
  Have a draft? Run:  python desi.py check README.md
  Not sure?     Run:  python desi.py wizard

Everything runs locally and reproducibly. No account, no setup, no jargon.
============================================================
"""


def cmd_home(_args) -> int:
    print(HOME)
    return 0


def cmd_check(args) -> int:
    if not args:
        print("usage: python desi.py check <file>")
        return 2
    import cli as paper_cli  # utility_evolution/paper_audit/cli.py
    return 0 if paper_cli.run(args[0]) >= 0 else 1


def cmd_decide(args) -> int:
    if not args:
        print('usage: python desi.py decide <options.json>\n'
              '  JSON: {"options":[...],"criteria":[{"name","weight","higher_is_better"}],'
              '"scores":{opt:{crit:0..1}}}')
        return 2
    import decide as dr  # utility_evolution/decision_record/decide.py
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    rec = dr.decide(spec["options"], spec["criteria"], spec["scores"])
    print(dr.format_record(rec))
    return 0


def cmd_memory(_args) -> int:
    import memory_explorer as me
    print(me.render(me.build()))
    return 0


def cmd_wizard(_args) -> int:  # pragma: no cover - interactive
    import wizard
    wizard.ask()
    return 0


COMMANDS = {"home": cmd_home, "check": cmd_check, "decide": cmd_decide,
            "memory": cmd_memory, "wizard": cmd_wizard}


def main(argv) -> int:
    if not argv:
        return cmd_home([])
    cmd, rest = argv[0], argv[1:]
    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    fn = COMMANDS.get(cmd)
    if fn is None:
        print(f"unknown command '{cmd}'. Try: {', '.join(COMMANDS)} (or no argument for Home).")
        return 2
    return fn(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
