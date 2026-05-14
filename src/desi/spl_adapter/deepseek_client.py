"""DeepSeekClient — v1.1 real-LLM call site, env-only key, fail-closed.

The client is the *only* place where the SPL touches a network. It is
deliberately a thin shim:

* the API key is read **exclusively** from the
  ``DEEPSEEK_API_KEY`` environment variable;
* a 10-second hard timeout is enforced on every HTTP call;
* up to 2 retries are attempted with exponential backoff (2s, 4s);
* responses larger than :data:`MAX_RESPONSE_SIZE_BYTES` are rejected;
* every error path raises :class:`BackendError` so the
  :class:`SPLAdapter` can fail-close from the same single boundary.

The HTTP layer is injectable. Production code points it at
``urllib.request.urlopen``; tests inject a callable that returns
canned bytes (or raises) without ever touching the network.

The client is **stateless** in audit terms: no API key is stored,
logged, or returned. The ledger never sees the key. The client never
prints the key to a debug log.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .errors import BackendError


# v1.1 directive: pinned model, pinned defaults, pinned timeout, pinned
# retry policy. None of these may drift between releases without an
# explicit code edit.
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL_ID = "deepseek-4-pro"
HARD_TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = (2.0, 4.0)
MAX_RESPONSE_SIZE_BYTES = 50 * 1024  # 50 KB
API_KEY_ENV_VAR = "DEEPSEEK_API_KEY"


HTTPTransport = Callable[[urllib.request.Request, float], bytes]
"""Signature of the injectable HTTP layer.

The callable receives a fully-constructed :class:`urllib.request.Request`
and a timeout, and returns the response body as ``bytes``. It may
raise :class:`TimeoutError`, :class:`urllib.error.URLError`, or any
other exception; the client converts them into :class:`BackendError`.
"""


def _urlopen_transport(req: urllib.request.Request, timeout: float) -> bytes:
    """Default production transport: urllib.request.urlopen."""
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(MAX_RESPONSE_SIZE_BYTES + 1)


@dataclass(frozen=True)
class DeepSeekResponse:
    """Successful response body. v1.1 keeps the surface narrow:
    callers only need the raw text payload (the LLM JSON of units)."""

    raw_text: str
    size_bytes: int


class DeepSeekClient:
    """Minimal client for DeepSeek 4 Pro chat completion.

    The client refuses to be constructed without a key in the
    environment unless ``allow_unset_key=True`` is passed (used only
    by the tests that drive the "missing key" fail-closed path).
    """

    def __init__(
        self,
        *,
        api_url: str = DEEPSEEK_API_URL,
        model_id: str = DEEPSEEK_MODEL_ID,
        temperature: float = 0.0,
        max_tokens: int = 512,
        timeout: float = HARD_TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
        retry_backoff: tuple[float, ...] = RETRY_BACKOFF_SECONDS,
        transport: HTTPTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        allow_unset_key: bool = False,
    ) -> None:
        self._api_url = api_url
        self._model_id = model_id
        self._temperature = float(temperature)
        self._max_tokens = int(max_tokens)
        self._timeout = float(timeout)
        self._max_retries = int(max_retries)
        self._retry_backoff = tuple(retry_backoff)
        self._transport: HTTPTransport = transport or _urlopen_transport
        self._sleep = sleep_fn
        self._allow_unset_key = allow_unset_key

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def timeout(self) -> float:
        return self._timeout

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    def __call__(self, prompt: str) -> str:
        """SemanticBackend-compatible call site.

        ``LLMSemanticBackend`` accepts a ``Callable[[str], str]`` for
        ``llm_call``; the client implements that protocol directly so
        callers wire it without writing a wrapper::

            from desi.spl_adapter import LLMSemanticBackend, SPLAdapter
            from desi.spl_adapter.deepseek_client import DeepSeekClient

            adapter = SPLAdapter(
                backend=LLMSemanticBackend(llm_call=DeepSeekClient()),
            )
        """
        response = self.complete(prompt)
        return response.raw_text

    def complete(self, prompt: str) -> DeepSeekResponse:
        api_key = os.environ.get(API_KEY_ENV_VAR, "")
        if not api_key and not self._allow_unset_key:
            raise BackendError(
                "missing_api_key",
                f"{API_KEY_ENV_VAR} is not set; refusing to make request",
            )

        body = json.dumps({
            "model": self._model_id,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        request = urllib.request.Request(
            self._api_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                raw_bytes = self._transport(request, self._timeout)
            except TimeoutError as exc:
                last_error = exc
                if attempt < self._max_retries:
                    self._sleep(self._backoff(attempt))
                    continue
                raise BackendError("timeout", str(exc)) from exc
            except urllib.error.HTTPError as exc:
                last_error = exc
                if attempt < self._max_retries and exc.code >= 500:
                    self._sleep(self._backoff(attempt))
                    continue
                raise BackendError(f"http_{exc.code}", str(exc)) from exc
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt < self._max_retries:
                    self._sleep(self._backoff(attempt))
                    continue
                raise BackendError("url_error", str(exc)) from exc
            except BackendError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt < self._max_retries:
                    self._sleep(self._backoff(attempt))
                    continue
                raise BackendError("transport_failed", str(exc)) from exc
            if len(raw_bytes) > MAX_RESPONSE_SIZE_BYTES:
                raise BackendError(
                    "response_too_large",
                    f"{len(raw_bytes)} bytes > "
                    f"{MAX_RESPONSE_SIZE_BYTES} byte cap",
                )
            try:
                text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise BackendError("invalid_encoding", str(exc)) from exc
            return DeepSeekResponse(raw_text=text, size_bytes=len(raw_bytes))

        # Should not be reachable — every branch above either returns
        # or raises.
        raise BackendError(
            "retry_exhausted",
            str(last_error) if last_error else "no transport response",
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _backoff(self, attempt: int) -> float:
        if attempt < len(self._retry_backoff):
            return self._retry_backoff[attempt]
        return self._retry_backoff[-1]


__all__ = [
    "API_KEY_ENV_VAR",
    "DEEPSEEK_API_URL",
    "DEEPSEEK_MODEL_ID",
    "DeepSeekClient",
    "DeepSeekResponse",
    "HARD_TIMEOUT_SECONDS",
    "HTTPTransport",
    "MAX_RESPONSE_SIZE_BYTES",
    "MAX_RETRIES",
    "RETRY_BACKOFF_SECONDS",
]
