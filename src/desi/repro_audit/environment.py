"""Aufgabe 5 — deterministic environment fingerprint.

Captures python version, platform, optional dependency
availability + versions, git commit and branch, and a small
set of relevant environment variables. Written to
``artifacts/v4_11/environment.json`` by the report builder.

The fingerprint is computed deterministically: same
environment -> same output -> same replay_hash. Different
environments produce different fingerprints that the v4.11
classifier consults when grading tool benchmark outcomes.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from dataclasses import dataclass


_OPTIONAL_DEPENDENCIES: tuple[str, ...] = (
    "sympy",
    "numpy",
    "scipy",
)


_RELEVANT_ENV_VARS: tuple[str, ...] = (
    "PYTHONHASHSEED",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONPATH",
    "DESI_ENV",
)


def _package_version(name: str) -> str | None:
    try:
        mod = __import__(name)
    except ImportError:
        return None
    return getattr(mod, "__version__", "unknown")


def _git_output(args: tuple[str, ...]) -> str | None:
    try:
        result = subprocess.run(
            ("git",) + args, capture_output=True,
            text=True, timeout=5, check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


@dataclass(frozen=True)
class EnvironmentFingerprint:
    python_version: str
    platform: str
    installed_optional_dependencies: tuple[str, ...]
    sympy_available: bool
    package_versions: dict[str, str | None]
    git_commit: str | None
    branch: str | None
    env_vars: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "python_version": self.python_version,
            "platform": self.platform,
            "installed_optional_dependencies":
                list(self.installed_optional_dependencies),
            "sympy_available": self.sympy_available,
            "package_versions": dict(self.package_versions),
            "git_commit": self.git_commit,
            "branch": self.branch,
            "env_vars": dict(self.env_vars),
        }


def fingerprint() -> EnvironmentFingerprint:
    versions = {
        name: _package_version(name)
        for name in _OPTIONAL_DEPENDENCIES
    }
    installed = tuple(
        name for name, v in versions.items() if v is not None
    )
    env_vars = {
        name: os.environ.get(name, "")
        for name in _RELEVANT_ENV_VARS
    }
    return EnvironmentFingerprint(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
        platform=platform.system(),
        installed_optional_dependencies=installed,
        sympy_available=versions.get("sympy") is not None,
        package_versions=versions,
        git_commit=_git_output(("rev-parse", "HEAD")),
        branch=_git_output(
            ("rev-parse", "--abbrev-ref", "HEAD"),
        ),
        env_vars=env_vars,
    )


__all__ = ["EnvironmentFingerprint", "fingerprint"]
