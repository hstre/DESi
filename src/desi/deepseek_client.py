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
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> str:
        """Send a chat-completion request.

        ``timeout`` and ``max_retries`` override the request-level defaults
        from ``Config`` for this call only. Used by the meta-analyzer to
        give the SKEPTICAL_AUDITOR role a longer timeout when v4-pro is
        the resolved auditor model (paper0 ablation showed v4-pro
        auditor calls run 90-150s).
        """
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
        effective_timeout = (
            self._config.timeout_seconds if timeout is None else timeout
        )
        effective_retries = (
            self._config.max_retries if max_retries is None else max_retries
        )

        last_error: Exception | None = None
        for attempt in range(1, effective_retries + 1):
            try:
                response = requests.post(
                    self._endpoint,
                    json=payload,
                    headers=headers,
                    timeout=effective_timeout,
                )
            except requests.RequestException as exc:
                last_error = exc
                _LOG.warning("DeepSeek request failed (attempt %d): %s", attempt, exc)
                if attempt < effective_retries:
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
                if attempt < effective_retries:
                    self._sleep_backoff(attempt)
                continue

            if response.status_code >= 400:
                # Non-transient. Surface a clean error.
                raise DeepSeekError(
                    f"DeepSeek HTTP {response.status_code}: {response.text[:500]}"
                )

            try:
                body = response.json()
                msg = body["choices"][0]["message"]
            except (ValueError, KeyError, IndexError) as exc:
                raise DeepSeekError(
                    f"Malformed DeepSeek response: {response.text[:500]}"
                ) from exc
            # v4-series models split output into reasoning_content + content.
            # When the model burns its budget on reasoning and the content
            # field is empty, fall back to reasoning_content rather than
            # silently returning ''. Without this fallback, v4-pro auditor
            # calls under heavy evidence load would produce empty audits.
            content = (msg.get("content") or "").strip()
            if not content:
                reasoning = (msg.get("reasoning_content") or "").strip()
                if reasoning:
                    content = reasoning
            return content

        raise DeepSeekError(
            f"DeepSeek call failed after {effective_retries} attempts: {last_error}"
        )

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        # 2s, 4s, 8s, 16s — matches the project Git policy for symmetry.
        time.sleep(2 ** attempt)
