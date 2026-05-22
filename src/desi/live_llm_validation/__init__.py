"""DESi v38.0 - OpenRouter Connector Layer (read-only evaluation).

Makes REAL live OpenRouter calls (public models catalog + live Granite
inference samples), preserves the raw responses, hashes them and makes
them replayable. LLM outputs are observed stochastic evidence, never
canonical truth; only the input layer is stochastic and all downstream
evaluation is deterministic over the captured outputs.
"""
from __future__ import annotations

from .model_registry import (
    ROLE_DEEPSEEK, ROLE_GRANITE, catalog, catalog_models,
    completion_price, model_for_role, model_present, pricing_for,
    prompt_price, roles,
)
from .openrouter_client import (
    api_key_present, chat_completion, list_models,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_INGESTED, VERDICT_PARTIAL,
    V380Report, api_response_capture, build_connectors_artifact,
    build_report, connector_metrics, governance_identity,
    model_version_visibility, raw_output_replayability,
    replay_stability, response_hash_integrity, samples,
)
from .response_capture import (
    PROVENANCE_LIVE, build_record, capture_response, captures_present,
    load_captures, write_captures,
)
from .response_hashing import content_hash, record_hash


__all__ = [
    "PROVENANCE_LIVE",
    "REPORT_VERDICTS",
    "ROLE_DEEPSEEK",
    "ROLE_GRANITE",
    "VERDICT_HALT",
    "VERDICT_INGESTED",
    "VERDICT_PARTIAL",
    "V380Report",
    "api_key_present",
    "api_response_capture",
    "build_connectors_artifact",
    "build_record",
    "build_report",
    "captures_present",
    "capture_response",
    "catalog",
    "catalog_models",
    "chat_completion",
    "completion_price",
    "connector_metrics",
    "content_hash",
    "governance_identity",
    "list_models",
    "load_captures",
    "model_for_role",
    "model_present",
    "model_version_visibility",
    "pricing_for",
    "prompt_price",
    "raw_output_replayability",
    "record_hash",
    "replay_stability",
    "response_hash_integrity",
    "roles",
    "samples",
    "write_captures",
]
