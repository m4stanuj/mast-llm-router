# MAST LLM Router — MCP Server

> **Task-aware LLM fallback router. 11 providers. 10 chains. $0/month.**  
> Works with Claude Code, Cursor, Windsurf, Continue.dev, Codex CLI, and any MCP-compatible client.
![CI](https://github.com/mast-anuj/mast-llm-router/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![MCP](https://img.shields.io/badge/MCP-compatible-green)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Cost](https://img.shields.io/badge/monthly%20cost-%240-success)
![Providers](https://img.shields.io/badge/providers-11-orange)

---

## What is this?

Most AI pipelines break when a provider hits a rate limit.  
This one doesn't.

`mast-llm-router` is a **task-aware fallback router** that:

- Detects what kind of task you're doing from your prompt
- Routes to the optimal model chain for that task
- Auto-falls to the next model if one fails, rate-limits, or returns garbage
- Caches semantically similar prompts to avoid repeat API hits
- Runs entirely on free-tier APIs — zero monthly cost

Built as part of [M4ST](https://github.com/mast-anuj) — a personal AI OS running on an RTX 2060 Super.

---

## Quick Demo

```
User: "Write a Python script to scrape Hacker News"
Router: Detected task → code
Chain:  kimi-k2 → qwen3-coder → mimo-pro → nvidia-deepseek → deepseek → sambanova
Result: Response from kimi-k2 in 1.2s (cache miss)
```

```
User: "yeh kya hai samjhao"
Router: Detected task → hinglish
Chain:  sarvam → gemini-flash → groq-llama → cerebras → openrouter → mistral
Result: Response in Hindi-English mix
```

---

## Features

| Feature | Detail |
|---|---|
| **11 providers** | Groq, Cerebras, Gemini, OpenRouter, SambaNova, DeepSeek, Together, NVIDIA NIM, Mistral, xAI/Grok, HuggingFace |
| **10 task chains** | speed, reason, code, vision, research, write, agent, pentest, hinglish, vision_reason |
| **6 models per chain** | Best-first, auto-falls to next on failure |
| **SMART_KEY detection** | Paste any API key — provider auto-detected by prefix |
| **Semantic cache** | Fuzzy match at 0.82 threshold, 500 entry LRU |
| **Thread-safe cooldowns** | Per-key 429/auth cooldown, not per-provider |
| **Both transports** | stdio (local) + HTTP (remote) |
| **$0/month** | 100% free-tier APIs |

---

## Task Chains

```
speed         →  groq → cerebras → gemini-flash → openrouter → sambanova → deepseek
reason        →  deepseek-r1 → nemotron → gemini-pro → openrouter → together → mistral
code          →  kimi-k2 → qwen3-coder → mimo-pro → nvidia → deepseek → sambanova
vision        →  gemini-vision → openrouter-vision → together-vision → ...
research      →  perplexity → gemini-pro → deepseek-r1 → openrouter → ...
write         →  gemini-pro → mistral → together → openrouter → groq → cerebras
agent         →  deepseek-r1 → gemini-pro → openrouter → together → groq → ...
pentest       →  nvidia-deepseek → nemotron → deepseek-r1 → glm → mistral → ...
hinglish      →  sarvam → gemini-flash → groq → cerebras → openrouter → mistral
vision_reason →  gemini-vision → openrouter-vision → together-vision → ...
```

---

## MCP Tools Exposed

| Tool | Description |
|---|---|
| `llm_chat` | Single-turn prompt → best model |
| `llm_chat_multi_turn` | Full conversation history support |
| `llm_detect_task` | Preview which chain will handle your prompt |
| `llm_router_status` | Provider health, key counts, cooldowns |
| `llm_list_providers` | All providers + chains in JSON |
| `llm_cache_control` | Cache stats or clear |

---

## Installation

### 1. Clone

```bash
git clone https://github.com/mast-anuj/mast-llm-router.git
cd mast-llm-router
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure keys

```bash
cp .env.example .env
# Edit .env — paste your free-tier API keys
```

> **SMART_KEY tip:** Just paste any key into `SMART_KEY_1`, `SMART_KEY_2`, etc.  
> The router detects the provider automatically from the key prefix.

### 4. Test it

```bash
python src/server.py --help
```

---

## Client Setup

### Claude Code

Add to `~/.claude/claude_desktop_config.json` (or via `claude mcp add`):

```json
{
  "mcpServers": {
    "mast-router": {
      "command": "python",
      "args": ["/absolute/path/to/mast-llm-router/src/server.py"]
    }
  }
}
```

Or one-liner:
```bash
claude mcp add mast-router python /absolute/path/to/mast-llm-router/src/server.py
```

### Cursor / Windsurf

Settings → MCP → Add Server:

```json
{
  "name": "mast-router",
  "type": "stdio",
  "command": "python",
  "args": ["/absolute/path/to/mast-llm-router/src/server.py"]
}
```

### Continue.dev

In `.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "mast-router",
      "command": "python",
      "args": ["/absolute/path/to/mast-llm-router/src/server.py"]
    }
  ]
}
```

### Codex CLI

```bash
codex --mcp-server "python /absolute/path/to/mast-llm-router/src/server.py"
```

### HTTP Mode (Antigravity, Magnus, remote clients)

```bash
python src/server.py --http --port 8000
```

Then point your client to: `http://localhost:8000/mcp`

---

## Environment Variables

| Variable | Description |
|---|---|
| `SMART_KEY_1` … `SMART_KEY_30` | Auto-detected keys (recommended) |
| `GROQ_API_KEY` | Groq (+ `_1` through `_20` for rotation) |
| `CEREBRAS_API_KEY` | Cerebras |
| `GEMINI_API_KEY` | Google Gemini |
| `OPENROUTER_API_KEY` | OpenRouter |
| `NVIDIA_API_KEY` | NVIDIA NIM |
| `SAMBANOVA_API_KEY` | SambaNova |
| `DEEPSEEK_API_KEY` | DeepSeek |
| `TOGETHER_API_KEY` | Together AI |
| `MISTRAL_API_KEY` | Mistral |
| `GROKAI_API_KEY` | xAI / Grok |
| `HUGGINGFACE_API_KEY` | HuggingFace |

---

## How Key Detection Works

```
gsk_...      → Groq
csk-...      → Cerebras
AIza...      → Gemini
sk-or-...    → OpenRouter
nvapi-...    → NVIDIA NIM
sk-...       → DeepSeek / Together / Mistral (length-based split)
xai-...      → Grok
hf_...       → HuggingFace
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  MCP Client                          │
│  (Claude Code / Cursor / Codex / Antigravity / …)   │
└────────────────────┬────────────────────────────────┘
                     │  stdio / HTTP
┌────────────────────▼────────────────────────────────┐
│              server.py  (FastMCP)                    │
│   llm_chat │ multi_turn │ detect_task │ status …     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           llm_fallback.py  (Core Router)             │
│                                                      │
│  ┌─────────────┐  ┌──────────┐  ┌─────────────────┐ │
│  │ Task Detect │  │  Cache   │  │  Key Manager    │ │
│  │  (keyword)  │  │  (fuzzy) │  │  (cooldown)     │ │
│  └──────┬──────┘  └──────────┘  └─────────────────┘ │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │            Task Chain Selector               │    │
│  │  speed/reason/code/vision/pentest/hinglish…  │    │
│  └──────┬──────────────────────────────────────┘    │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │         Fallback Loop (6 models)             │    │
│  │  Provider 1 → fail → Provider 2 → …         │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Free Tier Limits (as of 2026)

| Provider | Free RPM | Free TPD |
|---|---|---|
| Groq | 30 | 14,400 |
| Cerebras | 30 | ~1M |
| Gemini Flash | 15 | 1M |
| NVIDIA NIM | 40 | — |
| SambaNova | 10 | — |
| OpenRouter (free models) | varies | varies |
| DeepSeek | 50 | — |

---

## Project Structure

```
mast-llm-router/
├── src/
│   ├── server.py          # MCP server (FastMCP)
│   └── llm_fallback.py    # Core router logic
├── config/
│   ├── claude_code.json   # Claude Code config
│   └── cursor_windsurf.json
├── .env.example           # Key template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Part of M4ST Ecosystem

```
M4ST OS
├── llm_fallback.py     ← this repo
├── mcp_servers/        86 MCP tools
├── OpenWork            MCP-based AI workspace
├── CAI                 Pentest agent layer
└── voice / memory / browser automation
```

---

## More Docs

- [AGENTS.md](./AGENTS.md) — Guide for AI agents using this MCP server
- [CHANGELOG.md](./CHANGELOG.md) — Version history and roadmap

## License

MIT — use it, fork it, build on it.

---

*Built by [@mast-anuj](https://linkedin.com/in/mast-anuj) | RTX 2060 Super | Bareilly, India*  
*Zero VC money. Zero monthly cost. Full control.*
