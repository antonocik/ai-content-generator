# ✨ AI Content Generator

Generate blog posts, social captions, marketing emails, product descriptions and ads from a single API — or from the bundled web UI.

The service is **provider-agnostic**. Point it at OpenAI, Anthropic, or any OpenAI-compatible endpoint. It also ships with a built-in offline provider so the app runs with zero credentials.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="Tests" src="https://img.shields.io/badge/tests-10%20passed-3fb950?style=flat-square">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square">
</p>

## Features

| | |
|---|---|
| 🎯 **5 content types** | blog, social, email, product, ad |
| 🎨 **4 tones** | professional, casual, enthusiastic, technical |
| 🔌 **3 providers** | `local` (offline), `openai`, `anthropic` |
| 🖥️ **Web UI** | served at `/` — no build step, no npm |
| 🧪 **Tested** | 10 tests, no network required |
| 📄 **OpenAPI docs** | interactive at `/docs` |

## Quick start

```bash
git clone https://github.com/antonocik/ai-content-generator.git
cd ai-content-generator

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open <http://localhost:8000>. That is the whole setup — the default `local` provider needs no API key.

## Providers

### local (default)

Deterministic, offline template provider. Useful for local development, demos, and tests. It composes a structured draft from the request rather than pretending to be a language model.

### openai

```bash
export ACG_PROVIDER=openai
export ACG_API_KEY=sk-...
uvicorn app.main:app
```

Set `ACG_BASE_URL` to target any OpenAI-compatible server (Azure OpenAI, Ollama, vLLM, LM Studio, …):

```bash
export ACG_PROVIDER=openai
export ACG_BASE_URL=http://localhost:11434/v1
export ACG_API_KEY=ollama
export ACG_MODEL=llama3.1
```

### anthropic

```bash
export ACG_PROVIDER=anthropic
export ACG_API_KEY=sk-ant-...
export ACG_MODEL=claude-3-5-haiku-latest
```

See [`.env.example`](.env.example) for every variable.

## API

### `POST /api/generate`

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "remote work productivity",
    "content_type": "blog",
    "tone": "casual",
    "audience": "engineering managers",
    "keywords": ["async", "deep work"],
    "max_words": 300
  }'
```

```json
{
  "content": "Everything You Need to Know About remote work productivity\n\n...",
  "provider": "local",
  "model": "template-v1",
  "content_type": "blog",
  "tone": "casual",
  "word_count": 55,
  "prompt": null
}
```

| Field | Type | Notes |
|---|---|---|
| `topic` | string | required, 1–200 chars |
| `content_type` | enum | `blog` \| `social` \| `email` \| `product` \| `ad` |
| `tone` | enum | `professional` \| `casual` \| `enthusiastic` \| `technical` |
| `audience` | string? | optional |
| `keywords` | string[] | optional, max 20 |
| `max_words` | int | 20–2000, default 200 |

### `GET /health`

```json
{ "status": "ok", "provider": "local", "model": "template-v1", "ready": true }
```

`ready` is `false` when a network provider is selected but `ACG_API_KEY` is missing.

## Docker

```bash
docker build -t ai-content-generator .
docker run -p 8000:8000 -e ACG_PROVIDER=openai -e ACG_API_KEY=sk-... ai-content-generator
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

```
..........                                                               [100%]
10 passed in 0.24s
```

The suite exercises the real ASGI app through `httpx.ASGITransport`, so routing, validation and serialisation are all covered. No mocks, no network.

## Project layout

```
app/
  config.py      environment-driven settings
  prompts.py     prompt construction + offline generator
  providers.py   provider abstraction (local / openai / anthropic)
  schemas.py     pydantic request & response models
  main.py        FastAPI app, routes, embedded web UI
tests/
  test_api.py    end-to-end API tests
```

## Adding a provider

Subclass nothing — implement `generate(prompt, settings) -> str`, register it in `_PROVIDERS`, and it is picked up automatically:

```python
class MyProvider:
    name = "mine"

    async def generate(self, prompt: str, settings: Settings) -> str:
        return "..."

_PROVIDERS["mine"] = MyProvider()
```

## License

MIT — see [LICENSE](LICENSE).
