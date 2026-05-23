"""v3.121 — live runtime utilisation snapshot.

Reads ``/proc/loadavg``, ``/proc/stat``, and
``/proc/meminfo`` to estimate the current
CPU and memory utilisation without spawning any
external process.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .hardware import hardware_snapshot


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return ""


def _cpu_stat_jiffies() -> tuple[int, int]:
    """Return (busy, total) jiffies from
    /proc/stat's first ``cpu`` aggregate
    line."""
    raw = _read("/proc/stat")
    for line in raw.splitlines():
        if line.startswith("cpu "):
            fields = line.split()[1:]
            nums = [
                int(x) for x in fields
                if x.isdigit()
            ]
            if len(nums) >= 4:
                idle = nums[3]
                iowait = nums[4] if len(nums) > 4 else 0
                total = sum(nums)
                busy = total - idle - iowait
                return (busy, total)
    return (0, 0)


def cpu_utilisation(window_seconds: float = 0.5) -> float:
    a_busy, a_total = _cpu_stat_jiffies()
    time.sleep(window_seconds)
    b_busy, b_total = _cpu_stat_jiffies()
    dt = b_total - a_total
    if dt <= 0:
        return 0.0
    return _round((b_busy - a_busy) / dt)


def memory_utilisation() -> float:
    hs = hardware_snapshot()
    if hs.ram_total_bytes <= 0:
        return 0.0
    used = (
        hs.ram_total_bytes
        - hs.ram_available_bytes
    )
    return _round(used / hs.ram_total_bytes)


def load_average() -> tuple[
    float, float, float,
]:
    raw = _read("/proc/loadavg").split()
    try:
        return (
            _round(float(raw[0])),
            _round(float(raw[1])),
            _round(float(raw[2])),
        )
    except (IndexError, ValueError):
        return (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class RuntimeSnapshot:
    cpu_utilisation: float
    memory_utilisation: float
    load1: float
    load5: float
    load15: float

    def to_dict(self) -> dict[str, object]:
        return {
            "cpu_utilisation":
                self.cpu_utilisation,
            "memory_utilisation":
                self.memory_utilisation,
            "load1": self.load1,
            "load5": self.load5,
            "load15": self.load15,
        }


def snapshot(
    window_seconds: float = 0.5,
) -> RuntimeSnapshot:
    cpu = cpu_utilisation(window_seconds)
    mem = memory_utilisation()
    l1, l5, l15 = load_average()
    return RuntimeSnapshot(
        cpu_utilisation=cpu,
        memory_utilisation=mem,
        load1=l1, load5=l5, load15=l15,
    )


def bottleneck(
    rs: RuntimeSnapshot,
) -> str:
    """Closed enum: cpu, memory, balanced,
    idle."""
    if rs.cpu_utilisation > 0.80:
        return "cpu"
    if rs.memory_utilisation > 0.80:
        return "memory"
    if (
        rs.cpu_utilisation < 0.10
        and rs.memory_utilisation < 0.10
    ):
        return "idle"
    return "balanced"


__all__ = [
    "RuntimeSnapshot",
    "bottleneck",
    "cpu_utilisation",
    "load_average",
    "memory_utilisation",
    "snapshot",
]
