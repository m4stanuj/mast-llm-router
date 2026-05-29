# AGENTS.md — MAST LLM Router

> This file is automatically read by Claude Code, Codex CLI, Cursor Agent,
> and other AI coding assistants. It tells them how to use this repo's MCP tools effectively.

---

## What This Repo Does

`mast-llm-router` is a task-aware LLM fallback router exposed as an MCP server.
It routes prompts to the best free-tier AI model based on task type, with automatic
fallback across 13 provider routes and 10 task chains.

**Zero monthly cost. Zero vendor lock-in. Full local control.**

---

## MCP Tools — When to Use What

### `llm_chat` — Default tool for most tasks
Use for single-turn prompts. Set `task` for best results.

```
llm_chat(prompt="...", task="code")       # code generation
llm_chat(prompt="...", task="reason")     # analysis, math, logic
llm_chat(prompt="...", task="speed")      # quick facts, one-liners
llm_chat(prompt="...", task="write")      # essays, docs, emails
llm_chat(prompt="...", task="research")   # deep dives, summaries
llm_chat(prompt="...", task="pentest")    # security, recon, vuln analysis
llm_chat(prompt="...", task="hinglish")   # Hindi-English mixed output
llm_chat(prompt="...", task="auto")       # auto-detect (default)
```

### `llm_stream` — Long generation tasks
Use when output is >500 tokens. Streams progress in real time.
Best for: long code files, detailed reports, multi-section docs.

```
llm_stream(prompt="Write a full FastAPI server with auth", task="code", max_tokens=4096)
```

### `llm_batch` — Parallel multi-prompt workflows
Use when you need multiple LLM calls. Much faster than sequential calls.
Max 20 prompts, concurrency 1-5.

```
llm_batch(prompts=[
  {"id": "summary", "prompt": "Summarize: ...", "task": "write"},
  {"id": "review",  "prompt": "Review this code: ...", "task": "code"},
  {"id": "explain", "prompt": "Explain: ...", "task": "reason"}
], concurrency=3)
```

### `llm_chat_multi_turn` — Conversations with history
Use when context from prior messages matters.

```
llm_chat_multi_turn(messages=[
  {"role": "system", "content": "You are a security researcher."},
  {"role": "user",   "content": "What is SQL injection?"},
  {"role": "assistant", "content": "...prior response..."},
  {"role": "user",   "content": "Show me a detection query."}
], task="pentest")
```

### `llm_detect_task` — Debug routing decisions
Use before `llm_chat` if you're unsure which chain will be selected.

```
llm_detect_task(prompt="scan this target for open ports")
# Returns: {"detected_task": "pentest", "chain": ["nvidia", "deepseek-r1", ...]}
```

### `llm_router_status` — Check provider health
Use when calls are failing or slow. Shows which providers are cooled down.

```
llm_router_status(verbose=True)
```

### `llm_cache_control` — Manage the response cache
```
llm_cache_control(action="stats")   # view hit rate
llm_cache_control(action="clear")   # wipe cache
```

### `llm_list_providers` — See all available models
```
llm_list_providers(verbose=True)
```

---

## Task → Chain Reference

| Task | Best For | Top Models |
|---|---|---|
| `speed` | Quick answers, facts | Groq → Cerebras → Gemini Flash |
| `reason` | Logic, math, analysis | DeepSeek-R1 → Nemotron → Gemini Pro |
| `code` | Code gen, debugging | Kimi-K2 → Qwen3-Coder → MiMo-Pro |
| `vision` | Image understanding | Gemini Vision → OpenRouter |
| `research` | Deep research | Perplexity → Gemini Pro → DeepSeek-R1 |
| `write` | Prose, docs, emails | Gemini Pro → Mistral → Together |
| `agent` | Tool use, planning | DeepSeek-R1 → Gemini Pro → OpenRouter |
| `pentest` | Security, recon | NVIDIA NIM → Nemotron → DeepSeek-R1 |
| `hinglish` | Hindi-English output | Sarvam → Gemini Flash → Groq |
| `vision_reason` | Visual reasoning | Gemini Vision → OpenRouter |

---

## Key Patterns for Agents

### Pattern 1 — Research then write
```python
# Step 1: research
research = llm_chat(prompt=f"Research: {topic}", task="research", max_tokens=2048)

# Step 2: write based on research
article = llm_stream(prompt=f"Write article based on:\n{research}", task="write", max_tokens=4096)
```

### Pattern 2 — Parallel code review
```python
files = ["auth.py", "db.py", "api.py"]
llm_batch(prompts=[
  {"id": f, "prompt": f"Review {f} for bugs:\n{read(f)}", "task": "code"}
  for f in files
], concurrency=3)
```

### Pattern 3 — Check before call
```python
# Always check status if you get consecutive failures
status = llm_router_status(verbose=False)
# If provider shows ⏳ cooldown, next call auto-skips it
```

---

## Important Notes for AI Agents

1. **Never hardcode a provider name** — use `task` param, let the router decide
2. **Use `llm_batch` over loops** — 3-5x faster for multi-prompt workflows
3. **Cache is on by default** — set `use_cache=False` for unique/dynamic prompts
4. **Errors are returned as strings** — check if response starts with `"ERROR:"`
5. **`auto` task works** but explicit task = better model match = better output
6. **Cooldowns are automatic** — no need to retry manually, router handles it
7. **Max 20 prompts per batch** — split larger batches into chunks

---

## Repo Structure

```
src/
  server.py        # MCP server — edit this to add tools
  llm_fallback.py  # Core router — edit this to add providers/chains
tests/
  test_router.py   # Run: pytest tests/
config/
  claude_code.json       # Claude Code MCP config
  cursor_windsurf.json   # Cursor/Windsurf MCP config
```

---

## Running Locally

```bash
# stdio mode (Claude Code, Codex, Cursor)
python src/server.py

# HTTP mode (remote clients, Antigravity, Magnus)
python src/server.py --http --port 8000

# Test without MCP client
python src/llm_fallback.py
```

---

*Part of the M4ST ecosystem — [github.com/m4stanuj](https://github.com/m4stanuj)*
