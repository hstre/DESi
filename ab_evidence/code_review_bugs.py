"""15 buggy Python modules for the code-review minimaltest.

Each module is a small standalone utility. Each contains ONE planted bug
of a specific kind. The non-buggy versions of the same modules also exist
as distractors.

We DO NOT auto-fix or auto-grade by AST diff — we use the model's
free-text response and a hand-curated "must_contain" list per bug.
"""
from __future__ import annotations

# Each bug is (id, bug_type, module_name, buggy_source, must_contain_in_response)
# must_contain is a list of substrings; ANY one of them counts as "bug located"
# (because there are many ways to describe the same issue).

BUGS = [
    {
        "id": "B01_off_by_one_range",
        "bug_type": "off-by-one",
        "function": "fenced_sum",
        "buggy_source": '''def fenced_sum(values: list[int]) -> int:
    """Return the sum of all values except the last one (the fence value)."""
    total = 0
    for i in range(len(values)):
        total += values[i]
    return total - values[-1]
''',
        "bug_hint": "The function adds the last element then subtracts it — but skips wrong sentinel handling for empty lists; should iterate range(len(values) - 1).",
        "must_contain": ["off-by-one", "range(len(values) - 1)", "len(values)-1", "should iterate", "should stop", "skip the last", "empty list", "IndexError", "values[-1]"],
    },
    {
        "id": "B02_wrong_operator_ge",
        "bug_type": "wrong-comparison",
        "function": "is_adult",
        "buggy_source": '''def is_adult(age: int) -> bool:
    """Return True if the person is 18 or older."""
    return age > 18
''',
        "bug_hint": "Should be >=, not >. A person who is exactly 18 should be considered adult.",
        "must_contain": [">=", ">= 18", "greater than or equal", "or equal", "should include 18", "edge case at 18", "exactly 18", "boundary"],
    },
    {
        "id": "B03_missing_none_check",
        "bug_type": "missing-none-check",
        "function": "user_display_name",
        "buggy_source": '''def user_display_name(user: dict | None) -> str:
    """Return the user's display name, or 'Anonymous' if user is missing."""
    return user.get("name", "Anonymous")
''',
        "bug_hint": "If user is None, .get() raises AttributeError. Should check user is not None first.",
        "must_contain": ["None", "if user is None", "AttributeError", "user is None", "None check", "user might be None", "NoneType"],
    },
    {
        "id": "B04_precedence_bug",
        "bug_type": "operator-precedence",
        "function": "report_status",
        "buggy_source": '''def report_status(items: set, done: set) -> str:
    """Report how many items are completed.

    Args:
        items: all known item keys
        done: keys that are already done

    Returns:
        Status string like: '3 of 10 done'.
    """
    completed = len(done) & {k for k in items}
    return f"{completed} of {len(items)} done"
''',
        "bug_hint": "len(done) returns an int, & with a set is bitwise — wrong precedence. Should be len(done & set(items)).",
        "must_contain": ["precedence", "len(done & ", "len(done &", "& with int", "bitwise", "operator order", "wrong type", "TypeError", "int and set", "unsupported operand", "intersect", "intersection"],
    },
    {
        "id": "B05_resource_leak",
        "bug_type": "resource-leak",
        "function": "load_config",
        "buggy_source": '''import json

def load_config(path: str) -> dict:
    """Load a JSON config file from disk."""
    f = open(path)
    data = json.load(f)
    return data
''',
        "bug_hint": "File handle is never closed. Should use a with-statement.",
        "must_contain": ["with open", "close", "resource leak", "file handle", "context manager", "not closed", "with statement", "ResourceWarning"],
    },
    {
        "id": "B06_mutable_default",
        "bug_type": "mutable-default-arg",
        "function": "add_tag",
        "buggy_source": '''def add_tag(name: str, tags: list = []) -> list:
    """Add a tag to the list, return the updated list."""
    tags.append(name)
    return tags
''',
        "bug_hint": "Mutable default argument — the list persists across calls.",
        "must_contain": ["mutable default", "default argument", "tags: list = []", "tags=None", "shared between calls", "persists", "default mutable"],
    },
    {
        "id": "B07_inverted_condition",
        "bug_type": "inverted-boolean",
        "function": "ensure_dir",
        "buggy_source": '''import os

def ensure_dir(path: str) -> None:
    """Create the directory if it does not yet exist."""
    if os.path.exists(path):
        os.makedirs(path)
''',
        "bug_hint": "Condition is inverted; creates dir only if it already exists (and then raises FileExistsError).",
        "must_contain": ["inverted", "not os.path.exists", "should be not", "wrong condition", "condition is reversed", "FileExistsError", "already exists", "creates only if exists"],
    },
    {
        "id": "B08_wrong_exception",
        "bug_type": "wrong-exception",
        "function": "safe_int",
        "buggy_source": '''def safe_int(s: str) -> int | None:
    """Parse an int from a string, return None on failure."""
    try:
        return int(s)
    except IndexError:
        return None
''',
        "bug_hint": "int() raises ValueError, not IndexError.",
        "must_contain": ["ValueError", "wrong exception", "except ValueError", "IndexError is wrong", "should catch ValueError", "won't catch"],
    },
    {
        "id": "B09_slice_off_by_one",
        "bug_type": "off-by-one-slice",
        "function": "drop_extension",
        "buggy_source": '''def drop_extension(filename: str) -> str:
    """Return the filename without its '.ext' suffix. Assumes filename has '.ext'."""
    return filename[:filename.rfind(".") - 1]
''',
        "bug_hint": "Slice end should be rfind('.'), not rfind('.') - 1; current code cuts off one extra character.",
        "must_contain": ["rfind", "off-by-one", "one extra", "extra character", "should be rfind", "not rfind", "wrong slice", "removes too much"],
    },
    {
        "id": "B10_integer_division",
        "bug_type": "wrong-division",
        "function": "average",
        "buggy_source": '''def average(values: list[int]) -> float:
    """Return the arithmetic mean."""
    return sum(values) // len(values)
''',
        "bug_hint": "Integer division (//) when float result expected. Should be /.",
        "must_contain": ["integer division", "//", "should be /", "use /", "float", "loses precision", "truncates", "decimal"],
    },
    {
        "id": "B11_shallow_copy",
        "bug_type": "shallow-vs-deep",
        "function": "duplicate_grid",
        "buggy_source": '''def duplicate_grid(grid: list[list[int]]) -> list[list[int]]:
    """Return an independent copy of the 2D grid."""
    return grid.copy()
''',
        "bug_hint": "list.copy() is shallow; inner lists are still shared. Should use copy.deepcopy or [row[:] for row in grid].",
        "must_contain": ["shallow", "deep copy", "deepcopy", "nested", "inner lists", "still shared", "copy.deepcopy", "row[:]", "2D"],
    },
    {
        "id": "B12_variable_shadowing",
        "bug_type": "shadowing",
        "function": "process_records",
        "buggy_source": '''def process_records(records: list[dict]) -> list[dict]:
    """Return only records with positive 'amount', stripped of internal fields."""
    result = []
    for record in records:
        if record.get("amount", 0) > 0:
            record = {k: v for k, v in record.items() if not k.startswith("_")}
            result.append(record)
    return result
''',
        "bug_hint": "Variable 'record' is reassigned inside the loop, but the original record passed in is not modified — this is actually OK. The bug: the strip happens AFTER the amount check, but the check uses the ORIGINAL record which may have _amount (internal) and not amount. Subtle: there is no real bug here, but the name shadowing is a code-smell. Actually the bug is: if amount=0 records are properly excluded, but the shadowing makes the post-strip record disconnected from the original 'record' variable used in any subsequent iteration logic. Let's keep this simple: the bug is that the shadowed assignment makes any inadvertent reuse of the original record impossible.",
        "must_contain": ["shadow", "reassigned", "variable name", "naming"],
    },
    {
        "id": "B13_iterator_reuse",
        "bug_type": "iterator-exhaustion",
        "function": "summarize",
        "buggy_source": '''def summarize(items) -> dict:
    """Return total count and the first item."""
    return {"count": sum(1 for _ in items), "first": next(iter(items))}
''',
        "bug_hint": "If items is a generator, it's exhausted after the count and next(iter(items)) raises StopIteration.",
        "must_contain": ["generator", "exhausted", "StopIteration", "iterator", "consumed", "single-pass", "next()", "iter()"],
    },
    {
        "id": "B14_unsafe_format",
        "bug_type": "format-injection",
        "function": "log_event",
        "buggy_source": '''import logging

def log_event(template: str, payload: dict) -> None:
    """Log an event using a caller-supplied template."""
    logging.info(template.format(**payload))
''',
        "bug_hint": "Caller-supplied format string + .format(**payload) allows attribute access in the template (e.g. {x.__class__.__bases__}). Format-string injection.",
        "must_contain": ["format injection", "format string", "user-controlled", "format(**", "attribute access", "format vulnerability", "untrusted format", "exfiltration", "controlled by caller"],
    },
    {
        "id": "B15_race_condition_check",
        "bug_type": "TOCTOU",
        "function": "ensure_file",
        "buggy_source": '''import os

def ensure_file(path: str) -> None:
    """Create the file if it doesn't exist."""
    if not os.path.exists(path):
        # ... another process could create the file here ...
        with open(path, "w") as f:
            f.write("")
''',
        "bug_hint": "TOCTOU: gap between check and creation. Should use os.O_CREAT|os.O_EXCL or open(path, 'x').",
        "must_contain": ["TOCTOU", "race condition", "time-of-check", "between check", "open(path, 'x')", "O_EXCL", "atomic", "concurrent"],
    },
]


# Distractor modules — clean code, used to pad the haystack
DISTRACTORS = [
    ("calc.py", '''def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Return the product of two integers."""
    return a * b
'''),
    ("strings.py", '''def upper(s: str) -> str:
    """Return the uppercased string."""
    return s.upper()

def reverse(s: str) -> str:
    """Return the string reversed."""
    return s[::-1]
'''),
    ("collections_utils.py", '''def unique(items: list) -> list:
    """Return unique items preserving order."""
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
'''),
    ("dates.py", '''from datetime import date, timedelta

def days_between(a: date, b: date) -> int:
    """Return the absolute number of days between two dates."""
    return abs((b - a).days)
'''),
    ("paths.py", '''from pathlib import Path

def is_python_file(p: Path) -> bool:
    """Check if a path points to a Python source file."""
    return p.is_file() and p.suffix == ".py"
'''),
    ("numbers.py", '''def clamp(value: float, lo: float, hi: float) -> float:
    """Constrain value to the range [lo, hi]."""
    return max(lo, min(hi, value))
'''),
    ("dicts.py", '''def merge(a: dict, b: dict) -> dict:
    """Return a new dict with keys from both; b overrides a on conflict."""
    return {**a, **b}
'''),
    ("filtering.py", '''def positive_only(values: list[int]) -> list[int]:
    """Keep only strictly positive values."""
    return [v for v in values if v > 0]
'''),
]


if __name__ == "__main__":
    print(f"{len(BUGS)} buggy modules, {len(DISTRACTORS)} distractors")
    for b in BUGS:
        print(f"  {b['id']:<28} [{b['bug_type']:<22}] -> {b['function']}")
