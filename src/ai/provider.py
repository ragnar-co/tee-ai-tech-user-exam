"""AI provider layer: direct HTTPS to an OpenAI-compatible /chat/completions (OpenRouter).

Rules: no aix, no subprocess, no openai SDK (httpx only). The key is read from the environment,
sent only in the Authorization header and never logged, stored or put in an error message
(CON-21, GR-07).

Config (environment only; none stored in the DB):
  OPENAI_API_KEY, OPENAI_BASE_URL  required; either missing -> is_configured() is False.
  AI_TIMEOUT_SECONDS               optional; default DEFAULT_TIMEOUT_SECONDS (docs say null).
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.ai.prompt import build_messages

log = logging.getLogger(__name__)

PROVIDER_NAME = "openrouter"
MODEL_NAME = "anthropic/claude-sonnet-5"
DEFAULT_TIMEOUT_SECONDS = 60.0  # code default; override with AI_TIMEOUT_SECONDS


class AIProviderError(Exception):
    """Provider failure with a readable (Thai) message safe to show in the UI."""

    def __init__(self, message: str, *, status_code: int | None = None, kind: str = "error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.kind = kind


class ExecutiveSummaryProvider(ABC):
    @abstractmethod
    def generate(self, context: dict[str, Any]) -> str:
        """Return the draft text for the given context, or raise AIProviderError."""


def _status_message(status: int) -> tuple[str, str]:
    if status in (401, 403):
        return ("auth", f"AI provider ปฏิเสธคำขอ (HTTP {status}): ตรวจสอบ OPENAI_API_KEY หรือสิทธิ์/guardrail ของบัญชี")
    if status == 404:
        return ("not_found", "ไม่พบ endpoint หรือโมเดล (HTTP 404): ตรวจสอบ OPENAI_BASE_URL และชื่อโมเดล")
    if status == 429:
        return ("rate_limit", "เรียก AI provider ถี่เกินกำหนด (HTTP 429): กรุณารอสักครู่แล้วลองใหม่")
    if status >= 500:
        return ("server", f"AI provider ขัดข้องชั่วคราว (HTTP {status}): กรุณาลองใหม่ภายหลัง")
    return ("http", f"AI provider ตอบกลับผิดปกติ (HTTP {status})")


class OpenRouterProvider(ExecutiveSummaryProvider):
    provider_name = PROVIDER_NAME
    model_name = MODEL_NAME

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = (api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")).strip()
        self._base_url = (base_url if base_url is not None else os.environ.get("OPENAI_BASE_URL", "")).strip()
        if timeout is None:
            try:
                timeout = float(os.environ.get("AI_TIMEOUT_SECONDS", ""))
            except ValueError:
                timeout = DEFAULT_TIMEOUT_SECONDS
        self._timeout = timeout
        self._transport = transport

    def __repr__(self) -> str:  # never expose the key
        return f"OpenRouterProvider(model={MODEL_NAME!r}, configured={self.is_configured()})"

    def is_configured(self) -> bool:
        return bool(self._api_key and self._base_url)

    def missing_config_message(self) -> str:
        missing = [n for n, v in (("OPENAI_API_KEY", self._api_key), ("OPENAI_BASE_URL", self._base_url)) if not v]
        return "ยังไม่ได้ตั้งค่า " + " และ ".join(missing) + " จึงสร้าง AI Summary ไม่ได้ (ส่วน dashboard หลักใช้งานได้ตามปกติ)"

    def generate(self, context: dict[str, Any]) -> str:
        if not self.is_configured():
            raise AIProviderError(self.missing_config_message(), kind="not_configured")
        url = self._base_url.rstrip("/") + "/chat/completions"
        body = {"model": MODEL_NAME, "messages": build_messages(context)}
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                resp = client.post(url, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            log.warning("AI provider timeout (%s)", type(exc).__name__)
            raise AIProviderError("AI provider ไม่ตอบกลับภายในเวลาที่กำหนด (timeout): กรุณาลองใหม่", kind="timeout") from None
        except httpx.HTTPError as exc:
            log.warning("AI provider connection error (%s)", type(exc).__name__)
            raise AIProviderError("เชื่อมต่อ AI provider ไม่ได้: ตรวจสอบเครือข่ายและ OPENAI_BASE_URL", kind="connection") from None
        if resp.status_code != 200:
            kind, msg = _status_message(resp.status_code)
            log.warning("AI provider HTTP %d", resp.status_code)
            raise AIProviderError(msg, status_code=resp.status_code, kind=kind)
        try:
            text = resp.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            text = None
        if not isinstance(text, str) or not text.strip():
            log.warning("AI provider malformed response")
            raise AIProviderError("AI provider ตอบกลับในรูปแบบที่อ่านไม่ได้ (ไม่มีข้อความสรุป)", kind="malformed")
        return text.strip()
