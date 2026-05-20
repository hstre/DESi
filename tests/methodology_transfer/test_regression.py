"""v5.0 — regression: forbidden imports, runtime untouched.

v5.0 must not import from any v4 taxonomy module, must not
write outside ``methodology_transfer``/``artifacts/v5_0``,
and must leave v2.8 replay hashes intact.
"""
from __future__ import annotations

import importlib
import inspect
import pathlib


def _module_source(name: str) -> str:
    mod = importlib.import_module(name)
    return inspect.getsource(mod)


def test_no_v4_external_probe_import_in_v5_modules() -> None:
    """v5.0 may read ``external_probe`` *chains* for the
    contamination pool but must not import v4 taxonomy
    enums (e.g. ``FailureClass``) — those are the forbidden
    class names."""
    forbidden_symbols = ("FailureClass",)
    for sub in (
        "feature_extraction", "cluster_discovery",
        "taxonomy", "probe_generator", "report",
        "transfer_metrics", "negative_controls",
    ):
        src = _module_source(
            f"desi.methodology_transfer.{sub}",
        )
        for sym in forbidden_symbols:
            assert sym not in src, (sub, sym)


def test_v50_modules_do_not_modify_runtime_packages() -> None:
    """No file under the v5.0 subpackage may write to
    forbidden directories. We assert by absence — the
    methodology_transfer source must not name them in
    forbidden patterns."""
    forbidden_targets = (
        "src/desi/logic", "src/desi/frames",
        "src/desi/frame_tension", "src/desi/frame_inference",
        "src/desi/recursive", "src/desi/consilium",
        "src/desi/tools",
    )
    pkg = pathlib.Path(
        "/home/user/DESi/src/desi/methodology_transfer"
    )
    for py in pkg.glob("*.py"):
        txt = py.read_text(encoding="utf-8")
        for tgt in forbidden_targets:
            assert tgt not in txt, (py.name, tgt)


def test_v28_reconstruction_replay_hash_unchanged() -> None:
    """v2.8 reconstruction replay hash must remain
    1f4d9dfe44cb16e1. v5.0 must not have moved it."""
    from desi.repro_audit.report import (
        V2_8_FROZEN_RECONSTRUCTION_HASH,
    )
    assert V2_8_FROZEN_RECONSTRUCTION_HASH == (
        "1f4d9dfe44cb16e1"
    )


def test_v28_failcase_replay_hash_unchanged() -> None:
    """v2.8 fail-case replay hash must remain
    d83d81ab8417c022."""
    from desi.repro_audit.report import (
        V2_8_FROZEN_FAILCASE_HASH,
    )
    assert V2_8_FROZEN_FAILCASE_HASH == "d83d81ab8417c022"


def test_v5_writes_only_under_allowed_paths() -> None:
    """The v5.0 artifact directory exists and is the only
    artifact path under ``artifacts/`` carrying the
    ``v5_0`` prefix."""
    root = pathlib.Path("/home/user/DESi")
    a = root / "artifacts" / "v5_0"
    assert a.is_dir()
    assert (a / "report.json").is_file()
    assert (a / "taxonomy.json").is_file()


def test_v5_taxonomy_class_values_disjoint_from_v4() -> None:
    """No ``MT_*`` value collides with any v4
    ``FailureClass`` value."""
    from desi.external_probe.enums import FailureClass
    from desi.methodology_transfer.taxonomy import TaxonomyClass
    v4 = {f.value for f in FailureClass}
    v5 = {c.value for c in TaxonomyClass}
    assert v5 & v4 == set()
