"""v3.121 — hardware reality probe.

Closed sources, all read-only, no installation:

* ``os.cpu_count()`` and ``/proc/cpuinfo``
* ``/proc/meminfo``
* cgroup v1 / v2 quota files
* ``platform.uname()``
* env variables for CI detection
"""
from __future__ import annotations

import os
import platform
import re
from dataclasses import dataclass
from functools import lru_cache


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


@dataclass(frozen=True)
class HardwareSnapshot:
    cpu_count: int
    cpu_model: str
    ram_total_bytes: int
    ram_available_bytes: int
    cgroup_cpu_quota: float
    cgroup_memory_limit_bytes: int
    kernel: str
    machine: str

    def to_dict(self) -> dict[str, object]:
        return {
            "cpu_count": self.cpu_count,
            "cpu_model": self.cpu_model,
            "ram_total_bytes":
                self.ram_total_bytes,
            "ram_available_bytes":
                self.ram_available_bytes,
            "cgroup_cpu_quota":
                self.cgroup_cpu_quota,
            "cgroup_memory_limit_bytes":
                self.cgroup_memory_limit_bytes,
            "kernel": self.kernel,
            "machine": self.machine,
        }


def _parse_meminfo() -> tuple[int, int]:
    raw = _read("/proc/meminfo")
    total = 0
    avail = 0
    for line in raw.splitlines():
        if line.startswith("MemTotal:"):
            m = re.search(r"(\d+)", line)
            if m:
                total = int(m.group(1)) * 1024
        elif line.startswith("MemAvailable:"):
            m = re.search(r"(\d+)", line)
            if m:
                avail = int(m.group(1)) * 1024
    return (total, avail)


def _cpu_model() -> str:
    raw = _read("/proc/cpuinfo")
    for line in raw.splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[
                -1
            ].strip()
    return "unknown"


def _cpu_count() -> int:
    raw = _read("/proc/cpuinfo")
    procs = sum(
        1 for line in raw.splitlines()
        if line.startswith("processor")
    )
    if procs > 0:
        return procs
    n = os.cpu_count()
    return n or 0


def _cgroup_cpu_quota() -> float:
    """cgroup v2: cpu.max ('quota period') or
    cgroup v1: cfs_quota_us / cfs_period_us.
    Returns -1.0 for unlimited."""
    v2 = _read("/sys/fs/cgroup/cpu.max").strip()
    if v2 and v2 != "":
        parts = v2.split()
        if parts and parts[0] == "max":
            return -1.0
        if len(parts) == 2:
            try:
                quota = int(parts[0])
                period = int(parts[1])
                if quota < 0 or period <= 0:
                    return -1.0
                return _round(quota / period)
            except ValueError:
                return -1.0
    v1_quota = _read(
        "/sys/fs/cgroup/cpu/cpu.cfs_quota_us",
    ).strip()
    v1_period = _read(
        "/sys/fs/cgroup/cpu/cpu.cfs_period_us",
    ).strip()
    if v1_quota and v1_period:
        try:
            quota = int(v1_quota)
            period = int(v1_period)
            if quota < 0 or period <= 0:
                return -1.0
            return _round(quota / period)
        except ValueError:
            return -1.0
    return -1.0


def _cgroup_memory_limit() -> int:
    v2 = _read("/sys/fs/cgroup/memory.max").strip()
    if v2:
        if v2 == "max":
            return -1
        try:
            return int(v2)
        except ValueError:
            return -1
    v1 = _read(
        "/sys/fs/cgroup/memory/"
        "memory.limit_in_bytes",
    ).strip()
    if v1:
        try:
            return int(v1)
        except ValueError:
            return -1
    return -1


@lru_cache(maxsize=1)
def hardware_snapshot() -> HardwareSnapshot:
    total, avail = _parse_meminfo()
    return HardwareSnapshot(
        cpu_count=_cpu_count(),
        cpu_model=_cpu_model(),
        ram_total_bytes=total,
        ram_available_bytes=avail,
        cgroup_cpu_quota=_cgroup_cpu_quota(),
        cgroup_memory_limit_bytes=(
            _cgroup_memory_limit()
        ),
        kernel=platform.release(),
        machine=platform.machine(),
    )


_CI_ENV_KEYS: tuple[str, ...] = (
    "GITHUB_ACTIONS", "RUNNER_NAME",
    "RUNNER_OS", "CI", "GITHUB_RUN_ID",
)


def runner_type() -> str:
    if os.environ.get(
        "GITHUB_ACTIONS",
    ) == "true":
        return "github_hosted_runner"
    if any(
        os.environ.get(k)
        for k in _CI_ENV_KEYS
    ):
        return "ci_unknown"
    return "non_ci_vm"


def detected_ci_env() -> dict[str, str]:
    return {
        k: os.environ.get(k, "")
        for k in _CI_ENV_KEYS
    }


__all__ = [
    "HardwareSnapshot",
    "detected_ci_env",
    "hardware_snapshot",
    "runner_type",
]
