"""v3.122 — closed sprint-mutation taxonomy.

Four kinds (directive § v3.122):

* ``CORE_MUTATION``      - touches StateVector,
  extractor, frame detector, or replay
  hash logic.
* ``GATE_MUTATION``      - introduces or
  modifies a deployed Concept Gate / rule
  that fires in production.
* ``ANALYSIS_ONLY``      - read-only audit
  module, new artifact, new test suite.
* ``DOCS_ONLY``          - decision document
  or comment update.

Each commit is classified by inspecting its
message plus the file paths it touched.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache


class MutationKind(str, Enum):
    CORE_MUTATION     = "core_mutation"
    GATE_MUTATION     = "gate_mutation"
    ANALYSIS_ONLY     = "analysis_only"
    DOCS_ONLY         = "docs_only"


MUTATION_KINDS: tuple[str, ...] = tuple(
    k.value for k in MutationKind
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_CORE_PATH_PATTERNS: tuple[str, ...] = (
    "src/desi/epistemic_trajectory/extractor.py",
    "src/desi/epistemic_trajectory/state.py",
    "src/desi/frames/detector.py",
    "src/desi/frames/declaration.py",
)


def _classify_commit_files(
    files: tuple[str, ...], message: str,
) -> str:
    has_core = any(
        any(p in f for p in _CORE_PATH_PATTERNS)
        for f in files
    )
    if has_core:
        return MutationKind.CORE_MUTATION.value
    has_src = any(
        f.startswith("src/desi/") for f in files
    )
    has_test = any(
        f.startswith("tests/") for f in files
    )
    has_artifact = any(
        f.startswith("artifacts/") for f in files
    )
    if not (has_src or has_test or has_artifact):
        return MutationKind.DOCS_ONLY.value
    if "rule" in message.lower() and (
        "deploy" in message.lower()
        or "activated" in message.lower()
    ):
        return MutationKind.GATE_MUTATION.value
    # Any src/desi/ commit that does NOT touch
    # the closed core-path list is ANALYSIS_ONLY:
    # it adds a new audit package whose
    # downstream effect is bounded by its own
    # tests.
    return MutationKind.ANALYSIS_ONLY.value


def _git_log() -> tuple[
    tuple[str, str, tuple[str, ...]], ...,
]:
    """Returns ((sha, message, (files,)) for
    every commit reachable from HEAD, oldest
    first."""
    proc = subprocess.run(
        [
            "git", "log",
            "--format=__COMMIT__%H|%s",
            "--name-only",
            "--reverse",
        ],
        capture_output=True, text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ()
    out: list[
        tuple[str, str, tuple[str, ...]],
    ] = []
    sha = ""
    msg = ""
    files: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith("__COMMIT__"):
            if sha:
                out.append((
                    sha, msg, tuple(files),
                ))
            head = line[len("__COMMIT__"):]
            if "|" in head:
                sha, msg = head.split("|", 1)
            else:
                sha = head
                msg = ""
            files = []
        elif line.strip():
            files.append(line.strip())
    if sha:
        out.append((sha, msg, tuple(files)))
    return tuple(out)


@dataclass(frozen=True)
class CommitClassification:
    sha: str
    message: str
    file_count: int
    mutation_kind: str

    def to_dict(self) -> dict[str, object]:
        return {
            "sha": self.sha,
            "message": self.message,
            "file_count": self.file_count,
            "mutation_kind":
                self.mutation_kind,
        }


@lru_cache(maxsize=1)
def all_classified_commits() -> tuple[
    CommitClassification, ...,
]:
    out: list[CommitClassification] = []
    for sha, msg, files in _git_log():
        kind = _classify_commit_files(
            files, msg,
        )
        out.append(CommitClassification(
            sha=sha[:12],
            message=msg,
            file_count=len(files),
            mutation_kind=kind,
        ))
    return tuple(out)


__all__ = [
    "CommitClassification",
    "MUTATION_KINDS",
    "MutationKind",
    "all_classified_commits",
]
