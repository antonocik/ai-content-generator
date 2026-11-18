"""FastAPI application for the AI content generator."""

from __future__ import annotations

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from . import providers
from .config import Settings
from .prompts import build_prompt
from .schemas import GenerateRequest, GenerateResponse, HealthResponse

app = FastAPI(
    title="AI Content Generator",
    description="Generate blog posts, social captions, emails, product copy and ads.",
    version="1.0.0",
)

_settings = Settings.from_env()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_settings() -> Settings:
    return _settings


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    ready = settings.provider == "local" or bool(settings.api_key)
    return HealthResponse(
        status="ok",
        provider=settings.provider,
        model=settings.model,
        ready=ready,
    )


@app.post("/api/generate", response_model=GenerateResponse, tags=["generate"])
async def generate_content(
    request: GenerateRequest,
    settings: Settings = Depends(get_settings),
) -> GenerateResponse:
    try:
        content = await providers.generate(
            settings,
            topic=request.topic,
            content_type=request.content_type,
            tone=request.tone,
            audience=request.audience,
            keywords=request.keywords,
            max_words=request.max_words,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"provider error: {exc.response.status_code}")
    except (httpx.HTTPError, RuntimeError, KeyError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    prompt = None
    if settings.provider != "local":
        prompt = build_prompt(
            request.topic,
            request.content_type,
            request.tone,
            request.audience,
            request.keywords,
            request.max_words,
        )

    return GenerateResponse(
        content=content,
        provider=settings.provider,
        model=settings.model,
        content_type=request.content_type,
        tone=request.tone,
        word_count=len(content.split()),
        prompt=prompt,
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Content Generator</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; min-height:100vh; background:#0d1117; color:#e6edf3;
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:760px; margin:0 auto; padding:48px 20px 80px; }
  h1 { font-size:1.9rem; margin:0 0 6px; }
  p.sub { color:#8b949e; margin:0 0 28px; }
  form { display:grid; gap:14px; background:#161b22; border:1px solid #30363d;
         border-radius:12px; padding:22px; }
  label { font-size:.85rem; color:#8b949e; display:block; margin-bottom:6px; }
  input, select, textarea { width:100%; padding:10px 12px; border-radius:8px;
         border:1px solid #30363d; background:#0d1117; color:#e6edf3; font:inherit; }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  button { margin-top:6px; padding:12px; border:0; border-radius:8px; cursor:pointer;
           background:linear-gradient(135deg,#58a6ff,#a371f7); color:#0d1117;
           font-weight:700; font-size:1rem; }
  button:disabled { opacity:.6; cursor:progress; }
  pre { white-space:pre-wrap; background:#161b22; border:1px solid #30363d;
        border-radius:12px; padding:18px; margin-top:22px; }
  .meta { color:#8b949e; font-size:.8rem; margin-top:8px; }
  @media (max-width:560px){ .row { grid-template-columns:1fr; } }
</style>
</head>
<body>
<div class="wrap">
  <h1>✨ AI Content Generator</h1>
  <p class="sub">Blog posts, social captions, emails, product copy and ads.</p>
  <form id="f">
    <div>
      <label for="topic">Topic</label>
      <input id="topic" value="remote work productivity" required>
    </div>
    <div class="row">
      <div>
        <label for="type">Content type</label>
        <select id="type">
          <option value="blog">Blog post</option>
          <option value="social">Social media</option>
          <option value="email">Email</option>
          <option value="product">Product description</option>
          <option value="ad">Advertisement</option>
        </select>
      </div>
      <div>
        <label for="tone">Tone</label>
        <select id="tone">
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="enthusiastic">Enthusiastic</option>
          <option value="technical">Technical</option>
        </select>
      </div>
    </div>
    <div>
      <label for="audience">Audience (optional)</label>
      <input id="audience" placeholder="busy engineering managers">
    </div>
    <div>
      <label for="keywords">Keywords (comma separated)</label>
      <input id="keywords" placeholder="focus, async, deep work">
    </div>
    <button type="submit">Generate</button>
  </form>
  <pre id="out" hidden></pre>
  <div class="meta" id="meta"></div>
</div>
<script>
const f = document.getElementById('f'), out = document.getElementById('out'),
      meta = document.getElementById('meta'), btn = f.querySelector('button');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  btn.disabled = true; btn.textContent = 'Generating…'; out.hidden = true; meta.textContent = '';
  const payload = {
    topic: document.getElementById('topic').value,
    content_type: document.getElementById('type').value,
    tone: document.getElementById('tone').value,
    audience: document.getElementById('audience').value || null,
    keywords: document.getElementById('keywords').value.split(',').map(s=>s.trim()).filter(Boolean),
  };
  try {
    const res = await fetch('/api/generate', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'request failed');
    out.textContent = data.content; out.hidden = false;
    meta.textContent = `${data.word_count} words · ${data.provider}/${data.model}`;
  } catch (err) {
    out.textContent = 'Error: ' + err.message; out.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = 'Generate';
  }
});
</script>
</body>
</html>"""
