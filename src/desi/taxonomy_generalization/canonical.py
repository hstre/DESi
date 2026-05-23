"""Aufgabe 3 — freeze the v5.0 + v5.1 canonical reference.

Reads ``artifacts/v5_0/taxonomy.json`` (8 ``MT_*`` class
centroids + member sizes) and
``artifacts/v5_1/cluster_mapping_matrix.json`` (per-run
canonical-presence matrix used to certify class stability).
v5.2 never rewrites either artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import pathlib


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V50 = _REPO_ROOT / "artifacts" / "v5_0"
_V51 = _REPO_ROOT / "artifacts" / "v5_1"


@dataclass(frozen=True)
class CanonicalClassRef:
    name: str
    size: int
    centroid: tuple[float, ...]


@dataclass(frozen=True)
class CanonicalReference:
    classes: tuple[CanonicalClassRef, ...]
    largest_cluster_fraction: float
    stability_presence: dict[str, dict[str, bool]]

    @property
    def class_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.classes)

    @property
    def dominant_name(self) -> str:
        return max(
            self.classes, key=lambda c: c.size,
        ).name

    def centroid_for(self, name: str) -> tuple[float, ...]:
        for c in self.classes:
            if c.name == name:
                return c.centroid
        raise KeyError(name)

    def to_dict(self) -> dict[str, object]:
        return {
            "classes": [
                {
                    "name": c.name, "size": c.size,
                    "centroid": list(c.centroid),
                }
                for c in self.classes
            ],
            "largest_cluster_fraction":
                self.largest_cluster_fraction,
        }


def load_canonical_reference() -> CanonicalReference:
    tax = json.loads(
        (_V50 / "taxonomy.json").read_text(
            encoding="utf-8",
        )
    )
    matrix = json.loads(
        (_V51 / "cluster_mapping_matrix.json").read_text(
            encoding="utf-8",
        )
    )
    classes: list[CanonicalClassRef] = []
    for entry in tax["taxonomy"]:
        classes.append(CanonicalClassRef(
            name=entry["taxonomy_name"],
            size=int(entry["size"]),
            centroid=tuple(
                float(x) for x in
                entry["representative_centroid"]
            ),
        ))
    return CanonicalReference(
        classes=tuple(classes),
        largest_cluster_fraction=float(
            tax["largest_cluster_fraction"]
        ),
        stability_presence=matrix[
            "canonical_presence_matrix"
        ],
    )


__all__ = [
    "CanonicalClassRef", "CanonicalReference",
    "load_canonical_reference",
]
