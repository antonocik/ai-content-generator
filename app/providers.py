"""Provider-agnostic text generation.

Every provider exposes the same ``generate`` coroutine, so the API layer
never needs to know which backend is configured.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from .config import Settings
from .prompts import build_prompt, generate_local


class Provider(Protocol):
    name: str

    async def generate(self, prompt: str, settings: Settings) -> str: ...


class OpenAICompatibleProvider:
    """Works with OpenAI and any OpenAI-compatible ``/chat/completions`` API."""

    name = "openai"

    async def generate(self, prompt: str, settings: Settings) -> str:
        if not settings.api_key:
            raise RuntimeError("ACG_API_KEY is required for the openai provider")
        base_url = (settings.base_url or "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": "You are a professional copywriter."},
                {"role": "user", "content": prompt},
            ],
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class AnthropicProvider:
    name = "anthropic"

    async def generate(self, prompt: str, settings: Settings) -> str:
        if not settings.api_key:
            raise RuntimeError("ACG_API_KEY is required for the anthropic provider")
        base_url = (settings.base_url or "https://api.anthropic.com").rstrip("/")
        payload = {
            "model": settings.model,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "x-api-key": settings.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.timeout) as client:
            response = await client.post(f"{base_url}/v1/messages", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return "".join(block["text"] for block in data["content"]).strip()


_PROVIDERS: dict[str, Provider] = {
    "openai": OpenAICompatibleProvider(),
    "anthropic": AnthropicProvider(),
}


def get_provider(settings: Settings) -> Provider | None:
    return _PROVIDERS.get(settings.provider)


async def generate(
    settings: Settings,
    *,
    topic: str,
    content_type: str,
    tone: str,
    audience: str | None = None,
    keywords: list[str] | None = None,
    max_words: int = 200,
) -> str:
    """Generate content, falling back to the offline template provider."""
    keywords = keywords or []
    provider = get_provider(settings)
    if provider is None:
        return generate_local(topic, content_type, tone, audience, keywords, max_words)

    prompt = build_prompt(topic, content_type, tone, audience, keywords, max_words)
    return await provider.generate(prompt, settings)
