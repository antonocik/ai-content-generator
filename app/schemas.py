"""Pydantic request and response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal["blog", "social", "email", "product", "ad"]
Tone = Literal["professional", "casual", "enthusiastic", "technical"]


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200, examples=["remote work productivity"])
    content_type: ContentType = "blog"
    tone: Tone = "professional"
    audience: str | None = Field(None, max_length=200)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    max_words: int = Field(200, ge=20, le=2000)


class GenerateResponse(BaseModel):
    content: str
    provider: str
    model: str
    content_type: ContentType
    tone: Tone
    word_count: int
    prompt: str | None = None


class HealthResponse(BaseModel):
    status: str
    provider: str
    model: str
    ready: bool
