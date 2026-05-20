"""Minimal DeepSeek chat-completion client with retry on transient failures.

We intentionally avoid the official SDK to keep dependencies small. DeepSeek's
HTTP API mirrors the OpenAI chat-completion schema closely enough for our
needs.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests

from .config import Config

_LOG = logging.getLogger(__name__)

_TRANSIENT_STATUS = {408, 425, 429, 500, 502, 503, 504}


class DeepSeekError(RuntimeError):
    """Raised when the DeepSeek API call ultimately fails."""


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class DeepSeekClient:
    def __init__(self, config: Config):
        self._config = config
        self._endpoint = f"{config.deepseek_base_url.rstrip('/')}/v1/chat/completions"

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        api_key = self._config.require_api_key()
        payload = {
            "model": model or self._config.deepseek_model,
            "messages": [m.to_dict() for m in messages],
            "temperature": (
                self._config.temperature if temperature is None else temperature
            ),
            "max_tokens": (
                self._config.max_tokens if max_tokens is None else max_tokens
            ),
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                response = requests.post(
                    self._endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self._config.timeout_seconds,
                )
            except requests.RequestException as exc:
                last_error = exc
                _LOG.warning("DeepSeek request failed (attempt %d): %s", attempt, exc)
                self._sleep_backoff(attempt)
                continue

            if response.status_code in _TRANSIENT_STATUS:
                last_error = DeepSeekError(
                    f"transient HTTP {response.status_code}: {response.text[:200]}"
                )
                _LOG.warning(
                    "DeepSeek transient error (attempt %d): HTTP %s",
                    attempt,
                    response.status_code,
                )
                self._sleep_backoff(attempt)
                continue

            if response.status_code >= 400:
                # Non-transient. Surface a clean error.
                raise DeepSeekError(
                    f"DeepSeek HTTP {response.status_code}: {response.text[:500]}"
                )

            try:
                body = response.json()
                return body["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError) as exc:
                raise DeepSeekError(
                    f"Malformed DeepSeek response: {response.text[:500]}"
                ) from exc

        raise DeepSeekError(
            f"DeepSeek call failed after {self._config.max_retries} attempts: {last_error}"
        )

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        # 2s, 4s, 8s, 16s — matches the project Git policy for symmetry.
        time.sleep(2 ** attempt)
