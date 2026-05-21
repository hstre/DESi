"""v35.0 - external dataset loader (network-free).

Loads external benchmark datasets from the local datasets directory.
By design the loader never touches the network: external data only
ever enters DESi as local files that are versioned, hashed and
replay-bound here. Dropping the published suite's files into this
directory makes the same pipeline run against them unchanged.

Honesty note: in this environment the datasets are locally-vendored
reference sets in the published families' formats. They are NOT live
downloads of the official suites and their scores are NOT official
leaderboard numbers. Every dataset carries its true provenance.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from .dataset_hashing import byte_hash, content_hash

_DATASET_DIR = pathlib.Path(__file__).resolve().parent / "datasets"

PROVENANCE_OFFLINE_REFERENCE = "offline_reference_dataset"
KNOWN_PROVENANCES: tuple[str, ...] = (
    PROVENANCE_OFFLINE_REFERENCE,
    "external_published_suite",
)


@dataclass(frozen=True)
class Dataset:
    name: str
    family: str
    version: str
    provenance: str
    license: str
    source_note: str
    byte_hash: str
    content_hash: str
    payload: dict

    def items(self) -> tuple[dict, ...]:
        raw = self.payload.get("tasks")
        if raw is None:
            raw = self.payload.get("branches", [])
        return tuple(raw)

    def is_live_download(self) -> bool:
        return self.provenance == "external_published_suite"

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "family": self.family,
            "version": self.version,
            "provenance": self.provenance,
            "license": self.license,
            "source_note": self.source_note,
            "byte_hash": self.byte_hash,
            "content_hash": self.content_hash,
            "item_count": len(self.items()),
        }


def network_free() -> bool:
    """The loader never opens a network connection - external data
    only enters via local files."""
    return True


def dataset_dir() -> pathlib.Path:
    return _DATASET_DIR


def available_datasets() -> tuple[str, ...]:
    return tuple(
        sorted(p.stem for p in _DATASET_DIR.glob("*.json"))
    )


@lru_cache(maxsize=None)
def load_dataset(name: str) -> Dataset:
    path = _DATASET_DIR / f"{name}.json"
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return Dataset(
        name=payload["name"],
        family=payload["family"],
        version=payload["version"],
        provenance=payload["provenance"],
        license=payload["license"],
        source_note=payload["source_note"],
        byte_hash=byte_hash(raw),
        content_hash=content_hash(payload),
        payload=payload,
    )


def load_all() -> tuple[Dataset, ...]:
    return tuple(load_dataset(n) for n in available_datasets())


__all__ = [
    "KNOWN_PROVENANCES",
    "PROVENANCE_OFFLINE_REFERENCE",
    "Dataset",
    "available_datasets",
    "dataset_dir",
    "load_all",
    "load_dataset",
    "network_free",
]
