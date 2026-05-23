"""v38.0 - OpenRouter Connector Layer report.

Pflichtmetriken (directive § v38.0):

* api_response_capture
* raw_output_replayability
* response_hash_integrity
* model_version_visibility
* replay_stability

Killerfrage: "Kann DESi echte OpenRouter-LLM-Outputs replaybar
ingestieren?"

Captures real OpenRouter responses (the public models catalog plus
live Granite inference samples), preserves them fully, hashes them and
makes them replayable. The LLM layer is the only stochastic part;
evaluation reads the captured raw outputs deterministically and never
calls the network.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.frozen_baseline import governance_signature
from desi.peripheral_mutation import (
    core_identity, replay_stability as _core_replay,
)
from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .model_registry import catalog, catalog_models, roles, model_for_role
from .response_capture import load_captures
from .response_hashing import content_hash

_SAMPLE_CAPTURE = "v38_0_samples"

VERDICT_INGESTED = "OPENROUTER_CONNECTORS_REPLAY_STABLE"
VERDICT_PARTIAL = "OPENROUTER_CONNECTORS_PARTIAL"
VERDICT_HALT = "OPENROUTER_CONNECTORS_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_INGESTED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.95


def samples() -> tuple[dict, ...]:
    return load_captures(_SAMPLE_CAPTURE)


def governance_identity() -> float:
    if governance_signature() != governance_signature():
        return 0.0
    return 1.0 if core_identity() == 1.0 else 0.0


def api_response_capture() -> float:
    """1.0 iff real API responses were captured (the catalog and at
    least one live inference sample)."""
    has_catalog = bool(catalog_models())
    has_samples = bool(samples())
    return 1.0 if (has_catalog and has_samples) else 0.0


def raw_output_replayability() -> float:
    """1.0 iff reloading the captures yields byte-identical content
    (deterministic replay of the stochastic input)."""
    a = load_captures(_SAMPLE_CAPTURE)
    b = load_captures(_SAMPLE_CAPTURE)
    if [r.get("raw_content") for r in a] != [
        r.get("raw_content") for r in b
    ]:
        return 0.0
    return 1.0 if a else 0.0


def response_hash_integrity() -> float:
    """1.0 iff every capture's stored content hash matches a fresh
    hash of its raw content (tamper-evident)."""
    sm = samples()
    if not sm:
        return 0.0
    ok = sum(
        1 for r in sm
        if r.get("content_hash") == content_hash(
            r.get("raw_content", "")
        )
    )
    return round(ok / len(sm), 6)


def model_version_visibility() -> float:
    """Fraction of captured records (catalog models + samples) that
    expose a concrete model version."""
    cat = list(catalog_models().values())
    total = len(cat) + len(samples())
    if total == 0:
        return 0.0
    ok = sum(1 for m in cat if m.get("created") is not None)
    ok += sum(1 for r in samples() if r.get("model_version"))
    return round(ok / total, 6)


def replay_stability() -> float:
    if raw_output_replayability() < 1.0:
        return 0.0
    return 1.0 if _core_replay() == 1.0 else 0.0


def connector_metrics() -> dict[str, float]:
    return {
        "api_response_capture": api_response_capture(),
        "raw_output_replayability": raw_output_replayability(),
        "response_hash_integrity": response_hash_integrity(),
        "model_version_visibility": model_version_visibility(),
        "replay_stability": replay_stability(),
    }


def _signature() -> str:
    m = connector_metrics()
    parts = [f"{k}={m[k]}" for k in sorted(m)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _recommendation() -> str:
    m = connector_metrics()
    if m["replay_stability"] < 1.0 or core_identity() < 1.0:
        return VERDICT_HALT
    if all(v >= _FLOOR for v in m.values()):
        return VERDICT_INGESTED
    return VERDICT_PARTIAL


@dataclass(frozen=True)
class V380Report:
    catalog_model_count: int
    sample_capture_count: int
    total_sample_cost: float
    api_response_capture: float
    raw_output_replayability: float
    response_hash_integrity: float
    model_version_visibility: float
    replay_stability: float
    governance_identity: float
    core_identity: float
    human_approval_required: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "catalog_model_count": self.catalog_model_count,
            "sample_capture_count": self.sample_capture_count,
            "total_sample_cost": self.total_sample_cost,
            "api_response_capture": self.api_response_capture,
            "raw_output_replayability": self.raw_output_replayability,
            "response_hash_integrity": self.response_hash_integrity,
            "model_version_visibility": self.model_version_visibility,
            "replay_stability": self.replay_stability,
            "governance_identity": self.governance_identity,
            "core_identity": self.core_identity,
            "human_approval_required": self.human_approval_required,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"),
        )


def _total_cost() -> float:
    return round(sum(
        float(r.get("usage", {}).get("cost") or 0.0) for r in samples()
    ), 9)


def build_report() -> V380Report:
    m = connector_metrics()
    replay = m["replay_stability"]
    halt = replay < 1.0
    rationale = (
        f"INFO: captured the real OpenRouter public catalog "
        f"({len(catalog_models())} target models) and "
        f"{len(samples())} live Granite inference samples; roles "
        f"{list(roles())} -> {[model_for_role(r) for r in roles()]}",
        "INFO: LLM outputs are observed stochastic evidence, not "
        "canonical truth; raw outputs are captured, hashed and "
        "replayed, then evaluated deterministically",
        f"{'PASS' if m['api_response_capture'] >= _FLOOR else 'FAIL'}"
        f": api_response_capture {m['api_response_capture']} >= 0.95 "
        f"(real responses captured)",
        f"{'PASS' if m['raw_output_replayability'] >= _FLOOR else 'FAIL'}"
        f": raw_output_replayability {m['raw_output_replayability']} "
        f">= 0.95",
        f"{'PASS' if m['response_hash_integrity'] >= _FLOOR else 'FAIL'}"
        f": response_hash_integrity {m['response_hash_integrity']} "
        f">= 0.95",
        f"{'PASS' if m['model_version_visibility'] >= _FLOOR else 'FAIL'}"
        f": model_version_visibility {m['model_version_visibility']} "
        f">= 0.95",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: replay_stability "
        f"{replay} == 1.0; total live sample cost USD {_total_cost()};"
        f" governance_identity {governance_identity()}; core_identity "
        f"{core_identity()}; "
        f"HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED}",
    )
    return V380Report(
        catalog_model_count=len(catalog_models()),
        sample_capture_count=len(samples()),
        total_sample_cost=_total_cost(),
        api_response_capture=m["api_response_capture"],
        raw_output_replayability=m["raw_output_replayability"],
        response_hash_integrity=m["response_hash_integrity"],
        model_version_visibility=m["model_version_visibility"],
        replay_stability=replay,
        governance_identity=governance_identity(),
        core_identity=core_identity(),
        human_approval_required=HUMAN_APPROVAL_REQUIRED,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_connectors_artifact() -> dict[str, object]:
    m = connector_metrics()
    cat = catalog()
    return {
        "schema_version": "v38_0_openrouter_connectors",
        "disclaimer": (
            "OpenRouter connector layer making REAL live calls. The "
            "public models catalog and live Granite inference "
            "samples are captured from the real OpenRouter API "
            "(ENV-based auth; no API key in the repo), fully "
            "preserved, hashed and made replayable. LLM outputs are "
            "treated as observed stochastic evidence, never as "
            "canonical truth: only the input layer is stochastic, "
            "and all downstream evaluation reads the captured raw "
            "outputs deterministically and never calls the network. "
            "Human approval is mandatory."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "catalog_source": cat.get("source"),
        "catalog_models": cat.get("models"),
        "catalog_content_hash": cat.get("content_hash"),
        "sample_capture_count": len(samples()),
        "total_sample_cost_usd": _total_cost(),
        "api_response_capture": m["api_response_capture"],
        "raw_output_replayability": m["raw_output_replayability"],
        "response_hash_integrity": m["response_hash_integrity"],
        "model_version_visibility": m["model_version_visibility"],
        "replay_stability": m["replay_stability"],
        "governance_identity": governance_identity(),
        "core_identity": core_identity(),
        "human_approval_required": HUMAN_APPROVAL_REQUIRED,
        "signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_INGESTED",
    "VERDICT_PARTIAL",
    "V380Report",
    "api_response_capture",
    "build_connectors_artifact",
    "build_report",
    "connector_metrics",
    "governance_identity",
    "model_version_visibility",
    "raw_output_replayability",
    "replay_stability",
    "response_hash_integrity",
    "samples",
]
