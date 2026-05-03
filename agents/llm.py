"""
agents/llm.py — Unified LLM caller for all LogSnap agents.

Supports:
  - Groq  (llama-3.1-70b-versatile, mixtral-8x7b) — fast, free tier
  - Gemini Flash (gemini-1.5-flash)                — large context, free tier

Usage:
    from agents.llm import call_llm, LLMProvider

    response = call_llm(
        prompt="Implement this Python function...",
        system="You are a senior Python developer.",
        provider=LLMProvider.GROQ,   # or GEMINI, or AUTO
    )
    print(response.text)
    print(response.provider, response.model, response.tokens_used)

Environment variables (load from .env):
    GROQ_API_KEY   — required for Groq
    GEMINI_API_KEY — required for Gemini
    GROQ_MODEL     — optional override (default: llama-3.1-70b-versatile)
    GEMINI_MODEL   — optional override (default: gemini-1.5-flash)
"""

import os
import time
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Load .env automatically ───────────────────────────────────────────────────

def _load_env() -> None:
    """Load .env from project root into os.environ if not already set."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_env()

# ── Config ────────────────────────────────────────────────────────────────────

GROQ_API_URL   = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DEFAULT_GROQ_MODEL   = os.environ.get("GROQ_MODEL",   "llama-3.1-70b-versatile")
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

MAX_RETRIES    = 3
RETRY_DELAY    = 5       # seconds between retries
MAX_TOKENS     = 4096
TEMPERATURE    = 0.2     # low = more deterministic code output


# ── Data structures ───────────────────────────────────────────────────────────

class LLMProvider(str, Enum):
    """Available LLM providers."""
    GROQ   = "groq"
    GEMINI = "gemini"
    AUTO   = "auto"   # tries Groq first, falls back to Gemini


@dataclass
class LLMResponse:
    """Structured response from any LLM provider."""
    text: str
    provider: str
    model: str
    tokens_used: int
    latency_ms: int


class LLMError(Exception):
    """Raised when all providers fail or keys are missing."""
    pass


# ── Groq caller ───────────────────────────────────────────────────────────────

def _call_groq(
    prompt: str,
    system: str,
    model: str,
    api_key: str,
) -> LLMResponse:
    """Call Groq's OpenAI-compatible chat completions endpoint."""
    import urllib.request
    import json

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens":  MAX_TOKENS,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latency_ms = int((time.monotonic() - t0) * 1000)

    text = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)

    return LLMResponse(
        text=text,
        provider="groq",
        model=model,
        tokens_used=tokens,
        latency_ms=latency_ms,
    )


# ── Gemini caller ─────────────────────────────────────────────────────────────

def _call_gemini(
    prompt: str,
    system: str,
    model: str,
    api_key: str,
) -> LLMResponse:
    """Call Google Gemini generateContent endpoint."""
    import urllib.request
    import json

    url = GEMINI_API_URL.format(model=model) + f"?key={api_key}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature":    TEMPERATURE,
            "maxOutputTokens": MAX_TOKENS,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latency_ms = int((time.monotonic() - t0) * 1000)

    candidate = data["candidates"][0]["content"]["parts"][0]["text"]
    tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)

    return LLMResponse(
        text=candidate,
        provider="gemini",
        model=model,
        tokens_used=tokens,
        latency_ms=latency_ms,
    )


# ── Retry wrapper ─────────────────────────────────────────────────────────────

def _with_retry(fn, *args, **kwargs) -> LLMResponse:
    """Call fn with exponential backoff on transient errors."""
    import urllib.error

    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status == 429:
                wait = RETRY_DELAY * attempt
                logger.warning("Rate limited (429). Waiting %ds (attempt %d/%d)...",
                               wait, attempt, MAX_RETRIES)
                time.sleep(wait)
            elif status in (500, 502, 503):
                wait = RETRY_DELAY * attempt
                logger.warning("Server error %d. Retrying in %ds (attempt %d/%d)...",
                               status, wait, attempt, MAX_RETRIES)
                time.sleep(wait)
            else:
                body = exc.read().decode("utf-8", errors="replace")
                raise LLMError(f"HTTP {status}: {body}") from exc
            last_error = exc
        except Exception as exc:
            logger.warning("LLM call failed: %s (attempt %d/%d)", exc, attempt, MAX_RETRIES)
            time.sleep(RETRY_DELAY)
            last_error = exc

    raise LLMError(f"All {MAX_RETRIES} attempts failed. Last error: {last_error}") from last_error


# ── Public interface ──────────────────────────────────────────────────────────

def call_llm(
    prompt: str,
    system: str = "You are a senior Python developer. Return only valid Python code.",
    provider: LLMProvider = LLMProvider.AUTO,
    model: Optional[str] = None,
) -> LLMResponse:
    """
    Call an LLM with the given prompt and system message.

    Args:
        prompt:   The user message / task description.
        system:   The system prompt / persona for the model.
        provider: Which backend to use (GROQ, GEMINI, or AUTO).
        model:    Optional model name override.

    Returns:
        LLMResponse with .text, .provider, .model, .tokens_used, .latency_ms

    Raises:
        LLMError: if all providers fail or the required API key is missing.
    """
    groq_key   = os.environ.get("GROQ_API_KEY",   "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if provider == LLMProvider.GROQ or provider == LLMProvider.AUTO:
        if groq_key and groq_key != "your_groq_api_key_here":
            groq_model = model or DEFAULT_GROQ_MODEL
            logger.info("Calling Groq (%s)...", groq_model)
            try:
                return _with_retry(_call_groq, prompt, system, groq_model, groq_key)
            except LLMError as exc:
                if provider == LLMProvider.GROQ:
                    raise
                logger.warning("Groq failed, falling back to Gemini: %s", exc)
        elif provider == LLMProvider.GROQ:
            raise LLMError("GROQ_API_KEY not set. Add it to your .env file.")

    if provider == LLMProvider.GEMINI or provider == LLMProvider.AUTO:
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            gemini_model = model or DEFAULT_GEMINI_MODEL
            logger.info("Calling Gemini (%s)...", gemini_model)
            return _with_retry(_call_gemini, prompt, system, gemini_model, gemini_key)
        elif provider == LLMProvider.GEMINI:
            raise LLMError("GEMINI_API_KEY not set. Add it to your .env file.")

    raise LLMError(
        "No LLM API keys configured.\n"
        "1. Copy .env.example → .env\n"
        "2. Add your GROQ_API_KEY from https://console.groq.com\n"
        "3. Or add GEMINI_API_KEY from https://aistudio.google.com"
    )


def extract_code(response_text: str) -> str:
    """
    Extract the first Python code block from an LLM response.

    Handles ```python ... ``` fences, plain ``` fences,
    and falls back to the raw text if no fences found.
    """
    import re
    # Try ```python ... ``` first
    match = re.search(r"```python\s*(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try plain ``` ... ```
    match = re.search(r"```\s*(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Return as-is
    return response_text.strip()
