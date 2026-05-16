"""v4.11 — environment fingerprint determinism + content."""
from __future__ import annotations

from desi.repro_audit import fingerprint


def test_fingerprint_is_deterministic() -> None:
    a = fingerprint()
    b = fingerprint()
    assert a.to_dict() == b.to_dict()


def test_fingerprint_records_required_fields() -> None:
    f = fingerprint().to_dict()
    required = {
        "python_version", "platform",
        "installed_optional_dependencies",
        "sympy_available", "package_versions",
        "git_commit", "branch", "env_vars",
    }
    assert required.issubset(set(f)), set(f)


def test_sympy_availability_is_booleans() -> None:
    f = fingerprint()
    assert isinstance(f.sympy_available, bool)
    # The installed_optional_dependencies list must include
    # 'sympy' iff sympy_available is True.
    if f.sympy_available:
        assert "sympy" in f.installed_optional_dependencies
    else:
        assert "sympy" not in f.installed_optional_dependencies
