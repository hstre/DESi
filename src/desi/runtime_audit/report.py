"""v3.121 — runtime reality audit report.

Pflichtmetriken (directive § v3.121):

* ``cpu_count``
* ``ram_gb``
* ``runner_type``
* ``mean_cpu_utilization``
* ``mean_memory_utilization``
* ``bottleneck``
* ``replay_stability``

Killerfrage: "Wird DESi gerade durch Erkenntnis
limitiert - oder durch zwei Kerne?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .hardware import (
    detected_ci_env,
    hardware_snapshot,
    runner_type,
)
from .runner import (
    bottleneck, snapshot,
)


_GB: int = 1024 * 1024 * 1024


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3121Report:
    cpu_count: int
    cpu_model: str
    ram_gb: float
    ram_available_gb: float
    cgroup_cpu_quota: float
    cgroup_memory_limit_gb: float
    kernel: str
    machine: str
    runner_type: str
    ci_env: dict[str, str]
    mean_cpu_utilization: float
    mean_memory_utilization: float
    load1: float
    load5: float
    load15: float
    bottleneck: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "cpu_count": self.cpu_count,
            "cpu_model": self.cpu_model,
            "ram_gb": self.ram_gb,
            "ram_available_gb":
                self.ram_available_gb,
            "cgroup_cpu_quota":
                self.cgroup_cpu_quota,
            "cgroup_memory_limit_gb":
                self.cgroup_memory_limit_gb,
            "kernel": self.kernel,
            "machine": self.machine,
            "runner_type": self.runner_type,
            "ci_env": self.ci_env,
            "mean_cpu_utilization":
                self.mean_cpu_utilization,
            "mean_memory_utilization":
                self.mean_memory_utilization,
            "load1": self.load1,
            "load5": self.load5,
            "load15": self.load15,
            "bottleneck": self.bottleneck,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        hardware_snapshot().to_dict(),
        runner_type(),
    )
    b = (
        hardware_snapshot().to_dict(),
        runner_type(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3121Report:
    hs = hardware_snapshot()
    rs = snapshot()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif hs.cpu_count <= 2:
        verdict = "CPU_CONSTRAINED"
    elif rs.cpu_utilisation > 0.80:
        verdict = "CPU_SATURATED"
    elif rs.memory_utilisation > 0.80:
        verdict = "MEMORY_SATURATED"
    else:
        verdict = "HEADROOM_AVAILABLE"

    # Cgroup limits above 1 TB are treated as
    # "effectively unlimited" - they correspond
    # to the kernel's sentinel value
    # (9_223_372_036_854_771_712).
    _UNLIMITED_BYTES = 1 << 50
    if (
        hs.cgroup_memory_limit_bytes < 0
        or hs.cgroup_memory_limit_bytes
        >= _UNLIMITED_BYTES
    ):
        mem_limit_gb = -1.0
    else:
        mem_limit_gb = _round(
            hs.cgroup_memory_limit_bytes / _GB,
        )

    rationale = (
        f"INFO: cpu_count {hs.cpu_count}",
        f"INFO: cpu_model {hs.cpu_model!r}",
        f"INFO: ram_total_gb "
        f"{_round(hs.ram_total_bytes / _GB)}",
        f"INFO: ram_available_gb "
        f"{_round(hs.ram_available_bytes / _GB)}",
        f"INFO: cgroup_cpu_quota "
        f"{hs.cgroup_cpu_quota} "
        f"(-1 = unlimited)",
        f"INFO: cgroup_memory_limit_gb "
        f"{mem_limit_gb} "
        f"(-1 = unlimited)",
        f"INFO: kernel {hs.kernel}",
        f"INFO: machine {hs.machine}",
        f"INFO: runner_type {runner_type()}",
        f"INFO: ci_env {detected_ci_env()}",
        f"INFO: mean_cpu_utilization "
        f"{rs.cpu_utilisation}",
        f"INFO: mean_memory_utilization "
        f"{rs.memory_utilisation}",
        f"INFO: load1/5/15 "
        f"{rs.load1}/{rs.load5}/{rs.load15}",
        f"INFO: bottleneck {bottleneck(rs)}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3121Report(
        cpu_count=hs.cpu_count,
        cpu_model=hs.cpu_model,
        ram_gb=_round(
            hs.ram_total_bytes / _GB,
        ),
        ram_available_gb=_round(
            hs.ram_available_bytes / _GB,
        ),
        cgroup_cpu_quota=hs.cgroup_cpu_quota,
        cgroup_memory_limit_gb=mem_limit_gb,
        kernel=hs.kernel,
        machine=hs.machine,
        runner_type=runner_type(),
        ci_env=detected_ci_env(),
        mean_cpu_utilization=rs.cpu_utilisation,
        mean_memory_utilization=(
            rs.memory_utilisation
        ),
        load1=rs.load1, load5=rs.load5,
        load15=rs.load15,
        bottleneck=bottleneck(rs),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_runtime_reality_audit_artifact(
) -> dict[str, object]:
    hs = hardware_snapshot()
    rs = snapshot()
    return {
        "schema_version":
            "v3_121_runtime_reality_audit",
        "hardware": hs.to_dict(),
        "runner_type": runner_type(),
        "ci_env": detected_ci_env(),
        "runtime": rs.to_dict(),
        "bottleneck": bottleneck(rs),
    }


__all__ = [
    "V3121Report",
    "build_report",
    "build_runtime_reality_audit_artifact",
]
