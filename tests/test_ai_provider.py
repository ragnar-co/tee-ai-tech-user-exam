"""T-A01..T-A05 (provider side). httpx.MockTransport only: no network, no real key."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx
import pytest

from src.ai.prompt import DRAFT_LABEL, PROMPT_VERSION, SYSTEM_PROMPT
from src.ai.provider import MODEL_NAME, AIProviderError, OpenRouterProvider

KEY = "sk-SENTINEL-DUMMY-0000"
BASE = "https://mock.example/api/v1"
CONTEXT = {
    "source_run_id": 1,
    "reference_date": "2026-09-15",
    "aggregates": {"overdue": 3, "open": 7},
    "top_overdue_actions": [
        {"action_id": "A1", "project_name": "P01 - X", "action_name": "ทดสอบ",
         "owner": "Owner-007", "due_date": "2026-09-01", "days_overdue": 14}
    ],
}


def make(handler, **kw):
    return OpenRouterProvider(api_key=KEY, base_url=BASE, transport=httpx.MockTransport(handler), **kw)


def ok_handler(captured):
    def h(request: httpx.Request):
        captured.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": " ร่าง (DRAFT) สรุป "}}]})
    return h


def test_success_request_shape():
    seen: list[httpx.Request] = []
    text = make(ok_handler(seen)).generate(CONTEXT)
    assert text == "ร่าง (DRAFT) สรุป"
    req = seen[0]
    assert str(req.url) == BASE + "/chat/completions"
    assert req.headers["authorization"] == f"Bearer {KEY}"
    body = json.loads(req.content)
    assert body["model"] == MODEL_NAME == "anthropic/claude-sonnet-5"
    assert [m["role"] for m in body["messages"]] == ["system", "user"]


def test_payload_has_owner_but_no_key_or_raw_csv():
    seen: list[httpx.Request] = []
    make(ok_handler(seen)).generate(CONTEXT)
    payload = seen[0].content.decode()
    assert "Owner-007" in payload
    assert KEY not in payload
    assert "action_id,project_name" not in payload  # no CSV header / raw file


def test_prompt_guardrails():
    for token in ("GR-01", "GR-02", "GR-03", "GR-04", "GR-05", "GR-06", "GR-07", "severity", "SLA", DRAFT_LABEL):
        assert token in SYSTEM_PROMPT
    assert PROMPT_VERSION


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 502, 503])
def test_http_errors_mapped(status, caplog):
    caplog.set_level(logging.DEBUG)
    p = make(lambda r: httpx.Response(status, text=f"boom {KEY}"))
    with pytest.raises(AIProviderError) as ei:
        p.generate(CONTEXT)
    assert ei.value.status_code == status
    assert str(status) in ei.value.message
    assert KEY not in ei.value.message
    assert KEY not in caplog.text


def test_timeout_and_connection_errors(caplog):
    caplog.set_level(logging.DEBUG)

    def timeout(r):
        raise httpx.ReadTimeout("slow", request=r)

    def conn(r):
        raise httpx.ConnectError("down", request=r)

    with pytest.raises(AIProviderError) as ei:
        make(timeout).generate(CONTEXT)
    assert ei.value.kind == "timeout"
    with pytest.raises(AIProviderError) as ei:
        make(conn).generate(CONTEXT)
    assert ei.value.kind == "connection"
    assert KEY not in caplog.text


@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"choices": [{"message": {"content": ""}}]}])
def test_malformed_response(payload):
    with pytest.raises(AIProviderError) as ei:
        make(lambda r: httpx.Response(200, json=payload)).generate(CONTEXT)
    assert ei.value.kind == "malformed"


def test_non_json_response():
    with pytest.raises(AIProviderError):
        make(lambda r: httpx.Response(200, text="<html>")).generate(CONTEXT)


@pytest.mark.parametrize("key,base,missing", [("", BASE, "OPENAI_API_KEY"), (KEY, "", "OPENAI_BASE_URL"), ("", "", "OPENAI_API_KEY")])
def test_missing_config_disables_without_http(key, base, missing):
    calls = []

    def h(r):
        calls.append(r)
        return httpx.Response(200)

    p = OpenRouterProvider(api_key=key, base_url=base, transport=httpx.MockTransport(h))
    assert not p.is_configured()
    assert missing in p.missing_config_message()
    with pytest.raises(AIProviderError):
        p.generate(CONTEXT)
    assert calls == []


def test_env_config(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", BASE)
    assert not OpenRouterProvider().is_configured()
    monkeypatch.setenv("OPENAI_API_KEY", KEY)
    p = OpenRouterProvider()
    assert p.is_configured()
    assert KEY not in repr(p)


def test_timeout_env(monkeypatch):
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "5")
    assert OpenRouterProvider(api_key=KEY, base_url=BASE)._timeout == 5.0


def test_no_key_in_repo_files():
    root = Path(__file__).resolve().parent.parent
    for f in list((root / "src").rglob("*.py")) + [root / ".env.example"]:
        assert KEY not in f.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=\n" in (root / ".env.example").read_text() + "\n"
