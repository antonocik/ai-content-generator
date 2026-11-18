"""Prompt construction and deterministic offline generation.

The local provider keeps the API usable and testable without network access
or credentials. It produces structured, plausible drafts from the request
itself rather than pretending to be a language model.
"""

from __future__ import annotations

import hashlib
import re

TONES = {
    "professional": "clear, credible and to the point",
    "casual": "friendly and conversational",
    "enthusiastic": "energetic and upbeat",
    "technical": "precise and detail-oriented",
}

TEMPLATES = {
    "blog": "blog post",
    "social": "social media post",
    "email": "marketing email",
    "product": "product description",
    "ad": "advertisement",
}

_HEADLINE_PREFIXES = [
    "A Practical Look at",
    "Why",
    "Everything You Need to Know About",
    "Getting Started with",
]

_SENTENCE_BANK = {
    "blog": [
        "It solves a problem most teams run into sooner or later.",
        "The details matter more than the headline suggests.",
        "Here is a short breakdown you can act on today.",
        "Start small, measure, then scale what works.",
    ],
    "social": [
        "Save this for later.",
        "Thread below.",
        "Curious what you think.",
        "Tag someone who needs this.",
    ],
    "email": [
        "Reply to this email and tell us what you think.",
        "No fluff, just the part that matters.",
        "Unsubscribe at any time.",
    ],
    "product": [
        "Built for people who care about the details.",
        "Ships with everything you need to start.",
        "Designed to last.",
    ],
    "ad": [
        "Try it free today.",
        "Limited availability.",
        "See the difference for yourself.",
    ],
}


def build_prompt(
    topic: str,
    content_type: str,
    tone: str,
    audience: str | None,
    keywords: list[str],
    max_words: int,
) -> str:
    """Render the instruction sent to a language model provider."""
    lines = [
        f"Write a {TEMPLATES.get(content_type, content_type)} about {topic}.",
        f"Tone: {TONES.get(tone, tone)}.",
    ]
    if audience:
        lines.append(f"Audience: {audience}.")
    if keywords:
        lines.append("Naturally include these keywords: " + ", ".join(keywords) + ".")
    lines.append(f"Keep it under {max_words} words.")
    lines.append("Return only the content, without commentary or preamble.")
    return "\n".join(lines)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def generate_local(
    topic: str,
    content_type: str,
    tone: str,
    audience: str | None,
    keywords: list[str],
    max_words: int,
) -> str:
    """Produce a deterministic draft without calling any external service."""
    seed = int(hashlib.sha256(f"{topic}|{content_type}|{tone}".encode()).hexdigest(), 16)
    prefix = _HEADLINE_PREFIXES[seed % len(_HEADLINE_PREFIXES)]
    title = f"{prefix} {topic}".strip()

    sentences = list(_SENTENCE_BANK.get(content_type, _SENTENCE_BANK["blog"]))
    if audience:
        sentences.insert(0, f"If you are {audience}, this is written for you.")
    if keywords:
        sentences.append("Key ideas: " + ", ".join(keywords) + ".")

    body: list[str] = [title, ""]
    if content_type in {"blog", "product", "email"}:
        body.append(f"## {title}")
        body.append("")

    words = 0
    for sentence in sentences:
        if words >= max_words:
            break
        body.append(sentence)
        words += len(sentence.split())
        if content_type == "social":
            body.append("")

    if content_type == "social":
        body.append("#" + _slug(topic).replace("-", ""))

    return "\n".join(body).strip()
