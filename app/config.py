"""Configuration loaded from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    """Runtime settings for the content generator.

    ``provider`` selects the backend. ``local`` needs no credentials and is
    the default so the service is usable out of the box.
    """

    provider: str = "local"
    model: str = "gpt-4o-mini"
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 30.0
    max_tokens: int = 1024
    temperature: float = 0.7
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        env = env if env is not None else os.environ
        provider = env.get("ACG_PROVIDER", "local").lower()
        default_model = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-latest",
            "local": "template-v1",
        }.get(provider, "template-v1")

        api_key = env.get("ACG_API_KEY")
        if api_key is None:
            api_key = {
                "openai": env.get("OPENAI_API_KEY"),
                "anthropic": env.get("ANTHROPIC_API_KEY"),
            }.get(provider)

        return cls(
            provider=provider,
            model=env.get("ACG_MODEL", default_model),
            api_key=api_key,
            base_url=env.get("ACG_BASE_URL"),
            timeout=float(env.get("ACG_TIMEOUT", "30")),
            max_tokens=int(env.get("ACG_MAX_TOKENS", "1024")),
            temperature=float(env.get("ACG_TEMPERATURE", "0.7")),
            cors_origins=_split(env.get("ACG_CORS_ORIGINS")) or ["*"],
        )
