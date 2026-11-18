"""Tests for the content generator. Run with: pytest -q"""

from __future__ import annotations

import httpx
import pytest

from app.config import Settings
from app.main import app
from app.prompts import build_prompt, generate_local
from app.providers import generate


@pytest.fixture
def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.anyio
async def test_health_reports_local_provider(client):
    async with client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "local"
    assert body["ready"] is True


@pytest.mark.anyio
async def test_generate_returns_content_for_each_type(client):
    async with client:
        for content_type in ["blog", "social", "email", "product", "ad"]:
            response = await client.post(
                "/api/generate",
                json={"topic": "remote work", "content_type": content_type},
            )
            assert response.status_code == 200, content_type
            body = response.json()
            assert body["content"].strip()
            assert body["content_type"] == content_type
            assert body["word_count"] > 0


@pytest.mark.anyio
async def test_generate_includes_keywords(client):
    async with client:
        response = await client.post(
            "/api/generate",
            json={"topic": "focus", "keywords": ["async", "deep work"]},
        )
    assert response.status_code == 200
    assert "deep work" in response.json()["content"]


@pytest.mark.anyio
async def test_generate_rejects_empty_topic(client):
    async with client:
        response = await client.post("/api/generate", json={"topic": ""})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_generate_rejects_unknown_content_type(client):
    async with client:
        response = await client.post(
            "/api/generate", json={"topic": "x", "content_type": "poem"}
        )
    assert response.status_code == 422


def test_local_generation_is_deterministic():
    first = generate_local("ai", "blog", "casual", None, [], 200)
    second = generate_local("ai", "blog", "casual", None, [], 200)
    assert first == second
    assert "ai" in first.lower()


def test_local_generation_respects_max_words():
    content = generate_local("ai", "blog", "casual", None, [], 20)
    assert len(content.split()) <= 40


def test_build_prompt_mentions_all_inputs():
    prompt = build_prompt("focus", "blog", "technical", "developers", ["async"], 300)
    assert "focus" in prompt
    assert "developers" in prompt
    assert "async" in prompt
    assert "300 words" in prompt


@pytest.mark.anyio
async def test_openai_provider_requires_api_key():
    settings = Settings(provider="openai", api_key=None)
    with pytest.raises(RuntimeError, match="ACG_API_KEY"):
        await generate(settings, topic="x", content_type="blog", tone="casual")


@pytest.mark.anyio
async def test_unknown_provider_falls_back_to_local():
    settings = Settings(provider="nonexistent")
    content = await generate(settings, topic="fallback", content_type="blog", tone="casual")
    assert content.strip()
