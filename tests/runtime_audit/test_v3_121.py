"""v3.121 - runtime reality audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.runtime_audit.hardware import (
    detected_ci_env,
    hardware_snapshot,
    runner_type,
)
from desi.runtime_audit.report import (
    build_report,
    build_runtime_reality_audit_artifact,
)
from desi.runtime_audit.runner import (
    bottleneck,
    cpu_utilisation,
    load_average,
    memory_utilisation,
    snapshot,
)


def test_cpu_count_positive() -> None:
    hs = hardware_snapshot()
    assert hs.cpu_count >= 1


def test_ram_total_positive() -> None:
    hs = hardware_snapshot()
    assert hs.ram_total_bytes > 0


def test_kernel_non_empty() -> None:
    assert hardware_snapshot().kernel != ""


def test_machine_non_empty() -> None:
    assert hardware_snapshot().machine != ""


def test_runner_type_in_closed_set() -> None:
    allowed = {
        "github_hosted_runner",
        "ci_unknown",
        "non_ci_vm",
    }
    assert runner_type() in allowed


def test_ci_env_keys_present() -> None:
    env = detected_ci_env()
    for k in (
        "GITHUB_ACTIONS", "RUNNER_NAME",
        "RUNNER_OS", "CI", "GITHUB_RUN_ID",
    ):
        assert k in env


def test_cpu_utilisation_in_unit_interval() -> None:
    u = cpu_utilisation(window_seconds=0.05)
    assert 0.0 <= u <= 1.0


def test_memory_utilisation_in_unit_interval() -> None:
    u = memory_utilisation()
    assert 0.0 <= u <= 1.0


def test_load_average_returns_three_floats() -> None:
    la = load_average()
    assert len(la) == 3
    for v in la:
        assert isinstance(v, float)


def test_bottleneck_in_closed_set() -> None:
    allowed = {
        "cpu", "memory", "balanced", "idle",
    }
    s = snapshot(window_seconds=0.05)
    assert bottleneck(s) in allowed


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CPU_CONSTRAINED",
        "CPU_SATURATED",
        "MEMORY_SATURATED",
        "HEADROOM_AVAILABLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_cgroup_memory_unlimited_normalised() -> None:
    """Cgroup limits >= 1 TiB are reported as
    -1.0 (unlimited) rather than the kernel
    sentinel value."""
    r = build_report()
    if r.cgroup_memory_limit_gb >= 0:
        # If a real limit was set, it must be
        # below 1 TiB (otherwise normalised).
        assert r.cgroup_memory_limit_gb < 1024


def test_artifact_has_hardware_and_runtime() -> None:
    art = build_runtime_reality_audit_artifact()
    assert "hardware" in art
    assert "runtime" in art
    assert "runner_type" in art


def test_artifact_report_matches_live_build() -> None:
    """The reality snapshot is sampled live, so
    most fields are intentionally per-host
    fingerprints (``cpu_model``, ``load*``,
    ``mean_*_utilization``) or per-host sizing
    (``cpu_count``, ``ram_gb``, ``kernel``,
    ``cgroup_*``). Only the DERIVED /
    classification fields are guaranteed to be
    stable across replays on any sufficiently
    similar Linux VM: ``runner_type`` (closed
    enum), ``ci_env`` (env-var fingerprint, empty
    off CI), ``machine`` (target arch),
    ``recommendation``, ``halt``, and
    ``replay_stability``."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_121" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    stable_keys = {
        "ci_env", "halt", "machine",
        "recommendation", "replay_stability",
        "runner_type",
    }
    for k in stable_keys:
        assert art[k] == live[k], k
