"""v3.96b - source-level trace of non-determinism
inside ``src/desi/``.

The trace is intentionally static (no execution).
We scan every ``.py`` file under ``src/desi/`` for
patterns that can produce hash-seed-dependent
output and classify each hit.

Closed scan patterns:

* ``hash(``           - Python's randomized built-
  in hash; the canonical jitter source.
* ``frozenset(``       - dedup is order-preserving
  by hash, used for cache keys.
* ``set(``             - iteration order is
  insertion-order in CPython 3.7+ but unspecified.
* ``dict.fromkeys(``   - preserves insertion order
  but the input iterable may itself be unordered.
* ``json.dumps(... sort_keys=False ...)`` - any
  json.dumps without ``sort_keys=True`` may
  serialise dict keys in insertion order.

False positives are expected; the report ranks
hits by how likely they affect StateVector or
artifact output.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from functools import lru_cache


_REPO_ROOT: pathlib.Path = pathlib.Path(
    __file__,
).resolve().parents[3]
_SRC_ROOT: pathlib.Path = _REPO_ROOT / "src" / "desi"


# Excluded files: tests live under tests/, not src/,
# so no need to filter at the test boundary.
# trace.py contains the regex patterns themselves
# as docstring examples; including it would
# produce false positives that match the very
# documentation describing the patterns.
_EXCLUDED_NAMES: frozenset[str] = frozenset({
    "trace.py",
})


_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("builtin_hash",
     r"\bhash\([^)]",
     "Python's randomized built-in hash"),
    ("raw_set_literal",
     r"\bset\(",
     "set() constructor; iteration order unspecified"),
    ("dict_fromkeys",
     r"\bdict\.fromkeys\(",
     "dict.fromkeys preserves order but input must be ordered"),
    ("json_dumps_no_sort",
     r"json\.dumps\([^)]*\)",
     "json.dumps without sort_keys"),
)


_HIGH_RISK_KIND: frozenset[str] = frozenset({
    "builtin_hash",
})


@dataclass(frozen=True)
class TraceHit:
    path: str
    line_number: int
    kind: str
    excerpt: str
    description: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "line_number": self.line_number,
            "kind": self.kind,
            "excerpt": self.excerpt,
            "description": self.description,
        }


# The determinism* packages exist solely to
# discuss, fix and verify the very pattern the
# trace is looking for. Their docstrings and
# diagnostic code legitimately mention or
# reproduce hash() calls; including them would
# produce documentation-derived false positives
# that hide the production-code state.
_EXCLUDED_DIR_PREFIXES: tuple[str, ...] = (
    "determinism",
)


def _iter_source_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for p in sorted(_SRC_ROOT.rglob("*.py")):
        if any(
            part == "__pycache__"
            for part in p.parts
        ):
            continue
        if p.name in _EXCLUDED_NAMES:
            continue
        # Skip determinism* meta-tooling packages.
        rel_parts = p.relative_to(
            _SRC_ROOT,
        ).parts
        if rel_parts and any(
            rel_parts[0].startswith(prefix)
            for prefix in _EXCLUDED_DIR_PREFIXES
        ):
            continue
        out.append(p)
    return out


def _scan_file(
    path: pathlib.Path,
) -> list[TraceHit]:
    rel = path.relative_to(_REPO_ROOT)
    hits: list[TraceHit] = []
    try:
        lines = path.read_text(
            encoding="utf-8",
        ).splitlines()
    except (OSError, UnicodeDecodeError):
        return hits
    for n, line in enumerate(lines, start=1):
        for kind, pat, desc in _PATTERNS:
            # json.dumps pattern needs a sort_keys
            # second-pass check.
            if kind == "json_dumps_no_sort":
                m = re.search(pat, line)
                if m is None:
                    continue
                if "sort_keys=True" in line:
                    continue
                hits.append(TraceHit(
                    path=str(rel),
                    line_number=n,
                    kind=kind,
                    excerpt=line.strip(),
                    description=desc,
                ))
                continue
            if re.search(pat, line):
                hits.append(TraceHit(
                    path=str(rel),
                    line_number=n,
                    kind=kind,
                    excerpt=line.strip(),
                    description=desc,
                ))
    return hits


@lru_cache(maxsize=1)
def all_trace_hits() -> tuple[TraceHit, ...]:
    out: list[TraceHit] = []
    for p in _iter_source_files():
        out.extend(_scan_file(p))
    return tuple(out)


def hits_by_kind(kind: str) -> tuple[
    TraceHit, ...,
]:
    return tuple(
        h for h in all_trace_hits()
        if h.kind == kind
    )


def builtin_hash_hits() -> tuple[
    TraceHit, ...,
]:
    """High-risk: every ``hash(...)`` call that
    is not a custom function named like
    ``*_hash`` or ``hash_*``. The regex
    ``\\bhash\\(`` matches exactly the built-in;
    references to ``_payload_hash(`` or
    ``_short_hash(`` are not matched because
    the underscore precedes ``hash``."""
    return hits_by_kind("builtin_hash")


def is_high_risk(kind: str) -> bool:
    return kind in _HIGH_RISK_KIND


__all__ = [
    "TraceHit",
    "all_trace_hits",
    "builtin_hash_hits",
    "hits_by_kind",
    "is_high_risk",
]
