"""Tests for DeepSeekClient — env-only key, timeout, retries, size cap."""
from __future__ import annotations

import os
import urllib.error
import urllib.request

import pytest

from desi.spl_adapter import BackendError, DeepSeekClient
from desi.spl_adapter.deepseek_client import (
    API_KEY_ENV_VAR,
    DEEPSEEK_MODEL_ID,
    HARD_TIMEOUT_SECONDS,
    MAX_RESPONSE_SIZE_BYTES,
    MAX_RETRIES,
)


@pytest.fixture
def with_api_key(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "sk-fake-key-for-tests")
    yield


@pytest.fixture
def without_api_key(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    yield


def _ok_transport(req: urllib.request.Request, timeout: float) -> bytes:
    return b'{"units": []}'


# ---------------------------------------------------------------------------
# Constants are pinned
# ---------------------------------------------------------------------------


def test_model_id_is_deepseek_4_pro() -> None:
    assert DEEPSEEK_MODEL_ID == "deepseek-4-pro"


def test_hard_timeout_is_ten_seconds() -> None:
    assert HARD_TIMEOUT_SECONDS == 10.0


def test_max_retries_is_two() -> None:
    assert MAX_RETRIES == 2


def test_max_response_size_is_fifty_kb() -> None:
    assert MAX_RESPONSE_SIZE_BYTES == 50 * 1024


# ---------------------------------------------------------------------------
# Env-only key handling
# ---------------------------------------------------------------------------


def test_missing_api_key_fail_closes(without_api_key) -> None:
    client = DeepSeekClient(transport=_ok_transport)
    with pytest.raises(BackendError) as exc:
        client.complete("Water boils at 100C.")
    assert exc.value.kind == "missing_api_key"


def test_present_api_key_unlocks_the_call(with_api_key) -> None:
    client = DeepSeekClient(transport=_ok_transport)
    response = client.complete("Water boils at 100C.")
    assert response.raw_text == '{"units": []}'


def test_client_does_not_store_key_as_attribute(with_api_key) -> None:
    """The key must not be cached on the instance."""
    client = DeepSeekClient(transport=_ok_transport)
    client.complete("x")
    for attr in vars(client).values():
        if isinstance(attr, str):
            assert "sk-fake" not in attr


# ---------------------------------------------------------------------------
# Timeout fail-closes after retries
# ---------------------------------------------------------------------------


def test_timeout_fail_closes_after_retries(with_api_key) -> None:
    attempts = [0]

    def _timeout(req, timeout):
        attempts[0] += 1
        raise TimeoutError("read timed out")

    client = DeepSeekClient(transport=_timeout, sleep_fn=lambda s: None)
    with pytest.raises(BackendError) as exc:
        client.complete("x")
    assert exc.value.kind == "timeout"
    # 1 initial attempt + MAX_RETRIES retries
    assert attempts[0] == 1 + MAX_RETRIES


def test_url_error_retries_with_backoff(with_api_key) -> None:
    sleeps: list[float] = []

    def _url_error(req, timeout):
        raise urllib.error.URLError("connection refused")

    client = DeepSeekClient(transport=_url_error,
                             sleep_fn=lambda s: sleeps.append(s))
    with pytest.raises(BackendError):
        client.complete("x")
    assert sleeps == [2.0, 4.0]   # exponential backoff per spec


def test_recovery_after_one_transient_failure(with_api_key) -> None:
    """A transient URLError followed by a good response → success."""
    attempts = [0]

    def _flaky(req, timeout):
        attempts[0] += 1
        if attempts[0] == 1:
            raise urllib.error.URLError("transient")
        return b'{"units": []}'

    client = DeepSeekClient(transport=_flaky, sleep_fn=lambda s: None)
    response = client.complete("x")
    assert response.raw_text == '{"units": []}'
    assert attempts[0] == 2


# ---------------------------------------------------------------------------
# HTTP errors: 5xx retries, 4xx do not
# ---------------------------------------------------------------------------


def test_http_500_retries_then_fail_closes(with_api_key) -> None:
    attempts = [0]

    def _http_500(req, timeout):
        attempts[0] += 1
        raise urllib.error.HTTPError(
            url="x", code=500, msg="server error", hdrs=None, fp=None,
        )

    client = DeepSeekClient(transport=_http_500, sleep_fn=lambda s: None)
    with pytest.raises(BackendError) as exc:
        client.complete("x")
    assert exc.value.kind == "http_500"
    assert attempts[0] == 1 + MAX_RETRIES


def test_http_401_does_not_retry(with_api_key) -> None:
    attempts = [0]

    def _http_401(req, timeout):
        attempts[0] += 1
        raise urllib.error.HTTPError(
            url="x", code=401, msg="unauthorized", hdrs=None, fp=None,
        )

    client = DeepSeekClient(transport=_http_401, sleep_fn=lambda s: None)
    with pytest.raises(BackendError) as exc:
        client.complete("x")
    assert exc.value.kind == "http_401"
    assert attempts[0] == 1  # no retries on 4xx


# ---------------------------------------------------------------------------
# Response size guard at the HTTP boundary
# ---------------------------------------------------------------------------


def test_oversized_response_fail_closes_at_the_client(with_api_key) -> None:
    big = b"x" * (MAX_RESPONSE_SIZE_BYTES + 100)

    def _big(req, timeout):
        return big

    client = DeepSeekClient(transport=_big, sleep_fn=lambda s: None)
    with pytest.raises(BackendError) as exc:
        client.complete("x")
    assert exc.value.kind == "response_too_large"


# ---------------------------------------------------------------------------
# Authorization header is set, body is JSON, model is fixed
# ---------------------------------------------------------------------------


def test_client_sends_authorization_header_and_json_body(with_api_key) -> None:
    captured: dict = {}

    def _capture(req, timeout):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        return b'{"units": []}'

    client = DeepSeekClient(transport=_capture)
    client.complete("Water boils at 100C.")
    # Authorization header
    auth = captured["headers"].get(
        "Authorization", captured["headers"].get("authorization", ""),
    )
    assert auth.startswith("Bearer ")
    # Body parses as JSON with the pinned model id
    import json
    body = json.loads(captured["body"])
    assert body["model"] == "deepseek-4-pro"
    assert isinstance(body["messages"], list)


# ---------------------------------------------------------------------------
# The client is SemanticBackend-compatible (callable[[str], str])
# ---------------------------------------------------------------------------


def test_client_is_callable_returning_str(with_api_key) -> None:
    client = DeepSeekClient(transport=_ok_transport)
    out = client("hello")
    assert isinstance(out, str)
    assert out == '{"units": []}'
