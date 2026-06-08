"""GSM-Symbolic G0 - network-free dataset loader.

Loads the locally-vendored, GSM-Symbolic-shaped fixtures from this
package's ``data`` directory. By design the loader never touches the
network: external data only ever enters as local files that are
versioned, hashed and replay-bound here, exactly like the v35
``external_benchmarks`` connector.

This package is deliberately self-contained and does NOT register into
``external_benchmarks.benchmark_registry``: that connector ships
committed golden artifacts (``artifacts/external_benchmarks/``) whose
exact dataset count and content hashes are asserted by tests and guarded
by an artifact-drift CI gate. Wiring GSM-Symbolic into that registry is a
follow-up (G0.1) that must regenerate those artifacts under local
execution. Only the pure hashing primitives are reused here.

Honesty note: these fixtures are locally authored in the published
family's shape. They are NOT live downloads of Apple's GSM-Symbolic
suite (github.com/apple/ml-gsm-symbolic), NOT Apple's actual items, and
NOT official leaderboard scores. Every dataset carries its true
provenance and an ``is_apple_data`` flag set to ``False``.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import byte_hash, content_hash

_DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"

PROVENANCE_OFFLINE_REFERENCE = "offline_reference_dataset"

# Variants of the GSM-Symbolic family that this connector understands.
VARIANT_MAIN = "main"
VARIANT_P1 = "p1"
VARIANT_P2 = "p2"
KNOWN_VARIANTS: tuple[str, ...] = (VARIANT_MAIN, VARIANT_P1, VARIANT_P2)

# Closed set of clause roles used by the P2 negative controls.
CLAUSE_ROLES: tuple[str, ...] = (
    "",
    "base",
    "noop",
    "load_bearing",
    "adversarial_similar",
)


@dataclass(frozen=True)
class GsmInstance:
    """One concrete instantiation of a template (a single question)."""

    template_id: str
    instance_id: str
    question: str
    answer: str
    answer_type: str
    clause_role: str

    def is_complete(self) -> bool:
        return (
            bool(self.template_id)
            and bool(self.instance_id)
            and bool(self.question)
            and bool(self.answer)
            and bool(self.answer_type)
            and self.clause_role in CLAUSE_ROLES
        )


@dataclass(frozen=True)
class GsmDataset:
    """A vendored GSM-Symbolic-shaped dataset, bound to its hashes."""

    name: str
    family: str
    variant: str
    version: str
    provenance: str
    license: str
    source_note: str
    is_apple_data: bool
    byte_hash: str
    content_hash: str
    payload: dict

    def instances(self) -> tuple[GsmInstance, ...]:
        out: list[GsmInstance] = []
        for tmpl in self.payload.get("templates", []):
            tid = str(tmpl["template_id"])
            atype = str(tmpl.get("answer_type", "integer"))
            for inst in tmpl.get("instances", []):
                out.append(GsmInstance(
                    template_id=tid,
                    instance_id=str(inst["instance_id"]),
                    question=str(inst["question"]),
                    answer=str(inst["answer"]),
                    answer_type=atype,
                    clause_role=str(inst.get("clause_role", "")),
                ))
        return tuple(out)

    def template_ids(self) -> tuple[str, ...]:
        return tuple(
            str(t["template_id"])
            for t in self.payload.get("templates", [])
        )

    def is_live_download(self) -> bool:
        return self.provenance != PROVENANCE_OFFLINE_REFERENCE

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "family": self.family,
            "variant": self.variant,
            "version": self.version,
            "provenance": self.provenance,
            "license": self.license,
            "source_note": self.source_note,
            "is_apple_data": self.is_apple_data,
            "byte_hash": self.byte_hash,
            "content_hash": self.content_hash,
            "template_count": len(self.template_ids()),
            "instance_count": len(self.instances()),
        }


def network_free() -> bool:
    """The loader never opens a network connection - external data only
    enters via local files."""
    return True


def data_dir() -> pathlib.Path:
    return _DATA_DIR


def available_datasets() -> tuple[str, ...]:
    return tuple(sorted(p.stem for p in _DATA_DIR.glob("*.json")))


@lru_cache(maxsize=None)
def load_dataset(name: str) -> GsmDataset:
    path = _DATA_DIR / f"{name}.json"
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    return GsmDataset(
        name=payload["name"],
        family=payload["family"],
        variant=payload["variant"],
        version=payload["version"],
        provenance=payload["provenance"],
        license=payload["license"],
        source_note=payload["source_note"],
        is_apple_data=bool(payload["is_apple_data"]),
        byte_hash=byte_hash(raw),
        content_hash=content_hash(payload),
        payload=payload,
    )


def load_all() -> tuple[GsmDataset, ...]:
    return tuple(load_dataset(n) for n in available_datasets())


__all__ = [
    "CLAUSE_ROLES",
    "KNOWN_VARIANTS",
    "PROVENANCE_OFFLINE_REFERENCE",
    "VARIANT_MAIN",
    "VARIANT_P1",
    "VARIANT_P2",
    "GsmDataset",
    "GsmInstance",
    "available_datasets",
    "data_dir",
    "load_all",
    "load_dataset",
    "network_free",
]
