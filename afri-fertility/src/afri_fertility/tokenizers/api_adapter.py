"""Count-only API adapters for Claude (Anthropic) and Gemini (Google).

Requires the [api] optional extra:
    pip install "afri-fertility[api]"

These adapters call the provider's token-counting endpoint and return
a raw count.  They do NOT return token strings (inspectable=False) because
the APIs are opaque — individual tokens are never exposed.

Registration is triggered by register_api_adapters().  If the relevant
package is not installed, or if the API key is not set in the environment,
the adapter registers as UnavailableAdapter so it is skipped gracefully
in study runs.
"""
from __future__ import annotations

import os
import warnings

from .base import REGISTRY, UnavailableAdapter


class ClaudeAPIAdapter:
    """Count tokens using Anthropic's count_tokens endpoint (non-inspectable)."""

    id = "anthropic/claude"
    family = "anthropic"
    vocab_size = None
    inspectable = False

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        from anthropic import Anthropic  # deferred: requires [api] extra
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def count(self, text: str) -> int:
        response = self._client.messages.count_tokens(
            model=self._model,
            messages=[{"role": "user", "content": text}],
        )
        return response.input_tokens

    def tokens(self, text: str) -> list[str] | None:
        return None


class GeminiAPIAdapter:
    """Count tokens using Google's count_tokens endpoint (non-inspectable)."""

    id = "google/gemini"
    family = "google"
    vocab_size = None
    inspectable = False

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        import google.generativeai as genai  # deferred: requires [api] extra
        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def count(self, text: str) -> int:
        model = self._genai.GenerativeModel(self._model_name)
        result = model.count_tokens(text)
        return result.total_tokens

    def tokens(self, text: str) -> list[str] | None:
        return None


_api_registered = False


def register_api_adapters(
    anthropic_api_key: str | None = None,
    gemini_api_key: str | None = None,
    claude_model: str = "claude-sonnet-4-6",
    gemini_model: str = "gemini-2.0-flash",
) -> None:
    """Register Claude and Gemini API adapters.

    Called automatically when afri_fertility detects the [api] extra is installed.
    Keys are read from ANTHROPIC_API_KEY / GEMINI_API_KEY (or GOOGLE_API_KEY)
    environment variables if not passed explicitly.

    Adapters register as UnavailableAdapter when:
    - The required package is not installed (anthropic / google-generativeai).
    - The API key is not set in the environment.
    """
    global _api_registered
    if _api_registered:
        return

    # --- Claude ---
    import importlib.util
    if importlib.util.find_spec("anthropic") is not None:
        key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if key:
            try:
                REGISTRY.register(ClaudeAPIAdapter(api_key=key, model=claude_model))
            except Exception as exc:
                warnings.warn(f"anthropic/claude unavailable: {exc}", stacklevel=2)
                REGISTRY.register(UnavailableAdapter(id="anthropic/claude", reason=str(exc)))
        else:
            REGISTRY.register(UnavailableAdapter(
                id="anthropic/claude",
                reason="ANTHROPIC_API_KEY not set",
            ))

    # --- Gemini ---
    try:
        _gemini_spec = importlib.util.find_spec("google.generativeai")
    except (ModuleNotFoundError, ValueError):
        _gemini_spec = None
    if _gemini_spec is not None:
        gkey = (
            gemini_api_key
            or os.environ.get("GEMINI_API_KEY", "")
            or os.environ.get("GOOGLE_API_KEY", "")
        )
        if gkey:
            try:
                REGISTRY.register(GeminiAPIAdapter(api_key=gkey, model=gemini_model))
            except Exception as exc:
                warnings.warn(f"google/gemini unavailable: {exc}", stacklevel=2)
                REGISTRY.register(UnavailableAdapter(id="google/gemini", reason=str(exc)))
        else:
            REGISTRY.register(UnavailableAdapter(
                id="google/gemini",
                reason="GEMINI_API_KEY (or GOOGLE_API_KEY) not set",
            ))

    _api_registered = True
