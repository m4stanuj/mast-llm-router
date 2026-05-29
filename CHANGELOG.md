# Changelog

All notable changes to `mast-llm-router` are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [6.0.1] — 2026-05-29

### Added
- M4ST ecosystem links in README.

### Changed
- Public positioning now consistently says 13 provider routes.

---

## [6.0.0] — 2026-05-29

### Added
- **MCP Server** (`src/server.py`) — full FastMCP wrapper exposing 8 tools
- **`llm_stream` tool** — real SSE streaming with `ctx.report_progress()` chunks
- **`llm_batch` tool** — up to 20 concurrent prompts via `asyncio.Semaphore`
- **`llm_detect_task` tool** — preview routing decision before sending prompt
- **`llm_cache_control` tool** — cache stats and clear via MCP
- **`llm_list_providers` tool** — all providers + chains as JSON
- **`llm_router_status` tool** — per-provider health, key counts, cooldowns
- **NVIDIA NIM** provider — DeepSeek-R1, Nemotron, GLM-4 models
- **Mistral** provider — mistral-large-latest
- **xAI / Grok** provider — grok-3-mini-fast
- **HuggingFace** provider — meta-llama/Llama-3.3-70B-Instruct
- **`pentest` task chain** — NVIDIA NIM → Nemotron → DeepSeek-R1 → GLM
- **`hinglish` task chain** — Sarvam → Gemini Flash → Groq → Cerebras
- **`vision_reason` task chain** — combined vision + reasoning models
- **SMART_KEY detection** — auto-detect provider from key prefix (30 slots)
- **Semantic cache** — fuzzy match at 0.82 threshold, 500-entry LRU
- **Thread-safe cooldowns** — per-key 429/auth cooldown tracking
- **GitHub Actions CI** — lint, import check, secret scan, pytest runner
- **`pyproject.toml`** — `pip install mast-llm-router` support
- **Unit tests** (`tests/test_router.py`) — 20+ tests, zero real keys needed
- **Client configs** — Claude Code, Cursor, Windsurf, Continue.dev, Codex CLI

### Changed
- Renamed project from `Nexus` → `M4ST` → `mast-llm-router` (public release)
- Provider route count: 7 → 13
- Task chains: 6 → 10
- Keys per provider: up to 20 (was 10)
- Cache size: 200 → 500 entries

### Fixed
- Race condition in cooldown tracking under concurrent load
- Gemini fallback not triggering when OpenAI-compat chain exhausted
- Cache pickle corruption on unexpected shutdown (now uses JSON + bg thread)

---

## [5.0.0] — 2026-01-15

### Added
- Initial multi-provider fallback router
- 7 providers: Groq, Cerebras, Gemini, OpenRouter, SambaNova, DeepSeek, Together
- 6 task chains: speed, reason, code, vision, research, write
- Basic LRU cache with exact-match lookup
- LangChain `get_llm()` compatibility shim

### Architecture
- Single file `llm_fallback.py`
- Part of M4ST personal AI OS (internal use)

---

## Roadmap

- [ ] `llm_stream` for Gemini (native streaming API)
- [ ] Per-provider token usage tracking
- [ ] Redis cache backend option
- [ ] Async-native `chat_complete_async()`
- [ ] Web dashboard for live provider health
- [ ] PyPI publish (`pip install mast-llm-router`)
