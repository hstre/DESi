"""Deterministic date arithmetic tool.

Handles three constrained patterns over ISO dates (YYYY-MM-DD):
  * "days between <date> and <date>"      -> int (absolute difference)
  * "<n> days after <date>"               -> ISO date
  * "<n> days before <date>"              -> ISO date

Anything else raises ValueError (a language problem for the model, not a guess).
"""
from __future__ import annotations

import datetime as _dt
import re

_DATE = r"(\d{4}-\d{2}-\d{2})"
_BETWEEN = re.compile(rf"between\s+{_DATE}\s+and\s+{_DATE}", re.I)
_OFFSET = re.compile(rf"(\d+)\s*days?\s*(after|before)\s+{_DATE}", re.I)


def _parse(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s)


def solve_date(text: str) -> int | str:
    m = _OFFSET.search(text)
    if m:
        n, direction, date = int(m.group(1)), m.group(2).lower(), _parse(m.group(3))
        delta = _dt.timedelta(days=n if direction == "after" else -n)
        return (date + delta).isoformat()

    m = _BETWEEN.search(text)
    if m:
        d1, d2 = _parse(m.group(1)), _parse(m.group(2))
        return abs((d2 - d1).days)

    raise ValueError("no recognizable date expression (need ISO YYYY-MM-DD)")
