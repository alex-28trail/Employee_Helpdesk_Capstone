"""AI integration through an OpenAI-compatible API - local Ollama by default (F5.1, F5.3, F5.4).

Flow: build prompt -> POST {AI_BASE_URL}/chat/completions with a JSON schema
      -> json.loads -> Pydantic validation -> AnalysisOutcome.
Invalid output gets one retry, then 502. Network/auth/rate-limit/provider problems -> 503,
timeouts -> 504. Nothing in this module touches the database, so an AI failure can never
damage a ticket.
"""
import json
import logging
import re
import time
from dataclasses import dataclass
from functools import lru_cache

import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas.ai import AIAnalysisResult
from app.services.prompts import PROMPT_VERSION, RESPONSE_FORMAT, build_messages

logger = logging.getLogger("helpdesk.ai")


# --- Errors: each carries the HTTP status the router returns and a UI-safe message ---
class AIServiceError(Exception):
    status_code = 502

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AIUnavailableError(AIServiceError):
    status_code = 503


class AITimeoutError(AIServiceError):
    status_code = 504


class AIInvalidOutputError(AIServiceError):
    status_code = 502


@dataclass(frozen=True)
class ChatReply:
    content: str
    model: str  # the model that actually answered (openrouter/free picks one at random)


@dataclass(frozen=True)
class AnalysisOutcome:
    result: AIAnalysisResult
    model_name: str
    prompt_version: str
    latency_ms: int


class OpenRouterClient:
    """Thin client for any OpenAI-compatible chat API. `transport` lets tests inject fakes."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        timeout_seconds: float,
        require_structured_output: bool = True,
        app_name: str = "",
        max_tokens: int = 1500,
        transport: httpx.BaseTransport | None = None,
    ):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens
        self.require_structured_output = require_structured_output
        self._api_key = api_key  # never logged, never returned
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        if app_name:
            headers["X-Title"] = app_name
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
            transport=transport,
        )

    def chat(self, messages: list[dict]) -> ChatReply:
        if not self._api_key:
            raise AIUnavailableError("The AI service is not configured. Set AI_API_KEY in the backend .env file.")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,          # consistent triage, little creativity
            "max_tokens": self.max_tokens,  # reasoning models spend part of this before answering
            "response_format": RESPONSE_FORMAT,
        }
        if self.require_structured_output:
            # OpenRouter: only use providers that honour response_format
            payload["provider"] = {"require_parameters": True}

        try:
            response = self._http.post("/chat/completions", json=payload)
        except httpx.ConnectTimeout as exc:
            raise AIUnavailableError("The AI service is not reachable. Make sure Ollama is running (ollama serve).") from exc
        except httpx.TimeoutException as exc:
            raise AITimeoutError(
                f"The AI model did not respond within {self.timeout_seconds:g} seconds. "
                "You can retry or triage the ticket manually."
            ) from exc
        except httpx.TransportError as exc:
            raise AIUnavailableError("The AI service is not reachable. Make sure Ollama is running (ollama serve).") from exc

        self._raise_for_status(response)

        try:
            body = response.json()
        except ValueError as exc:
            raise AIInvalidOutputError("The AI service returned an unexpected response format.") from exc

        if isinstance(body, dict) and body.get("error"):
            # Some upstream provider failures come back inside a 200 body
            raise AIUnavailableError("The AI provider failed to answer. Please retry shortly.")

        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIInvalidOutputError("The AI service returned an unexpected response format.") from exc
        if not isinstance(content, str) or not content.strip():
            if isinstance(choice, dict) and choice.get("finish_reason") == "length":
                raise AIInvalidOutputError(
                    "The AI model ran out of tokens before answering. Raise AI_MAX_TOKENS or pick a non-reasoning model."
                )
            raise AIInvalidOutputError("The AI model returned an empty answer.")

        return ChatReply(content=content, model=str(body.get("model") or self.model))

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        code = response.status_code
        if code < 400:
            return
        if code in (401, 403):
            raise AIUnavailableError("The AI service rejected the API key. Check AI_API_KEY in the backend .env file.")
        if code == 402:
            raise AIUnavailableError("The AI account has no credit for this model. Use a free model id.")
        if code == 429:
            raise AIUnavailableError("The AI service is rate-limited right now. Please retry in a minute.")
        if code == 404:
            raise AIUnavailableError("No AI model is currently available for this request. Check AI_MODEL.")
        if code == 408:
            raise AITimeoutError("The AI provider timed out. You can retry or triage the ticket manually.")
        raise AIUnavailableError(f"The AI service returned an error (HTTP {code}). Please retry shortly.")

    def health(self) -> dict:
        """Cheap check for GET /health: key present, provider reachable AND key accepted.

        Uses OpenRouter's GET /key, which needs a valid key (GET /models is public, so it would
        report "ok" even with a wrong key). Providers without /key fall back to GET /models.
        Does not spend any model tokens.
        """
        if not self._api_key:
            return {"status": "not_configured", "model": self.model, "detail": "AI_API_KEY is not set"}
        try:
            response = self._http.get("/key", timeout=5.0)
            if response.status_code == 404:  # not OpenRouter: /models usually needs auth elsewhere
                response = self._http.get("/models", timeout=5.0)
        except httpx.HTTPError:
            return {"status": "unavailable", "model": self.model, "detail": "AI provider not reachable (is Ollama running?)"}
        if response.status_code in (401, 403):
            return {"status": "unavailable", "model": self.model, "detail": "AI provider rejected AI_API_KEY"}
        if response.status_code >= 400:
            return {
                "status": "unavailable", "model": self.model,
                "detail": f"AI provider returned HTTP {response.status_code}",
            }
        # Ollama lists the locally pulled models; flag a model that hasn't been pulled yet.
        try:
            available = {m.get("id") for m in response.json().get("data", []) if isinstance(m, dict)}
        except (ValueError, AttributeError):
            available = set()
        if available and self.model not in available:
            return {
                "status": "unavailable", "model": self.model,
                "detail": f"Model '{self.model}' is not pulled. Run: ollama pull {self.model}",
            }
        return {"status": "ok", "model": self.model}


_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.I)


def _strip_fences(raw: str) -> str:
    return _FENCE.sub("", raw)


def _describe(exc: Exception) -> str:
    """Error summary for logs: field locations only, never the model's text."""
    if isinstance(exc, ValidationError):
        fields = sorted({".".join(str(p) for p in e["loc"]) or "<root>" for e in exc.errors()})
        return f"ValidationError fields={','.join(fields)}"
    return type(exc).__name__


class AIService:
    def __init__(self, client: OpenRouterClient, max_retries: int = 1):
        self.client = client
        self.max_retries = max_retries

    def analyze_ticket(self, title: str, description: str) -> AnalysisOutcome:
        messages = build_messages(title, description)
        attempts = 1 + self.max_retries
        started = time.perf_counter()

        for attempt in range(1, attempts + 1):
            reply = self.client.chat(messages)  # 503/504 propagate immediately; retrying won't help
            try:
                result = AIAnalysisResult.model_validate(json.loads(_strip_fences(reply.content)))
            except (json.JSONDecodeError, ValidationError) as exc:
                logger.warning(
                    "event=ai_output_invalid attempt=%s/%s model=%s reason=%s",
                    attempt, attempts, reply.model, _describe(exc),
                )
                continue
            return AnalysisOutcome(
                result=result,
                model_name=reply.model,
                prompt_version=PROMPT_VERSION,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

        raise AIInvalidOutputError(
            "The AI model returned output that failed validation, so nothing was saved. "
            "You can retry or triage the ticket manually."
        )

    def health(self) -> dict:
        return self.client.health()


@lru_cache
def get_ai_service() -> AIService:
    """FastAPI dependency. Tests replace it with app.dependency_overrides."""
    client = OpenRouterClient(
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        api_key=settings.ai_api_key,
        timeout_seconds=settings.ai_timeout_seconds,
        require_structured_output=settings.ai_require_structured_output,
        app_name=settings.ai_app_name,
        max_tokens=settings.ai_max_tokens,
    )
    return AIService(client, max_retries=settings.ai_max_retries)
