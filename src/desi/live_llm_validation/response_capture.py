"""v38.0 - capture and replay of raw OpenRouter responses.

`capture_response` is run only during the stochastic capture phase: it
makes a real OpenRouter call and returns a fully-preserved record
(raw content, model version, usage/cost, hashes, provenance). The
records are committed as JSON and become the deterministic replay
source; `load_captures` reads them back so all downstream evaluation
is deterministic and network-free.
"""
from __future__ import annotations

import json
import pathlib

from .openrouter_client import chat_completion
from .response_hashing import content_hash, record_hash

PROVENANCE_LIVE = "live_openrouter_capture"

_CAPTURES = pathlib.Path(__file__).resolve().parent / "captures"


def build_record(
    task_id: str,
    role: str,
    requested_model: str,
    messages: list[dict],
    response: dict,
) -> dict:
    """Turn a raw OpenRouter response into a preserved capture
    record. No interpretation - just full preservation + hashing."""
    choice = (response.get("choices") or [{}])[0]
    raw_content = (choice.get("message") or {}).get("content") or ""
    usage = response.get("usage") or {}
    record = {
        "task_id": task_id,
        "role": role,
        "requested_model": requested_model,
        "model_version": response.get("model", requested_model),
        "messages": messages,
        "raw_content": raw_content,
        "finish_reason": choice.get("finish_reason"),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "cost": usage.get("cost"),
        },
        "response_id": response.get("id"),
        "provenance": PROVENANCE_LIVE,
    }
    record["content_hash"] = content_hash(raw_content)
    record["record_hash"] = record_hash(record)
    return record


def capture_response(
    task_id: str,
    role: str,
    model: str,
    messages: list[dict],
    *,
    max_tokens: int = 256,
    temperature: float = 0.0,
) -> dict:
    """Live capture: real OpenRouter call -> preserved record."""
    response = chat_completion(
        model, messages,
        max_tokens=max_tokens, temperature=temperature,
    )
    return build_record(task_id, role, model, messages, response)


def write_captures(name: str, records: list[dict]) -> pathlib.Path:
    path = _CAPTURES / f"{name}.json"
    path.write_text(
        json.dumps(
            {"captures": records}, indent=2, sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return path


def load_captures(name: str) -> tuple[dict, ...]:
    path = _CAPTURES / f"{name}.json"
    if not path.exists():
        return ()
    data = json.loads(path.read_text(encoding="utf-8"))
    return tuple(data.get("captures", []))


def captures_present(name: str) -> bool:
    return bool(load_captures(name))


__all__ = [
    "PROVENANCE_LIVE",
    "build_record",
    "capture_response",
    "captures_present",
    "load_captures",
    "write_captures",
]
