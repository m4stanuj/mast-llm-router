# MAST LLM Router — Social Media Kit

> Ready-to-use posts, hashtags, and captions for sharing the project.

---

## Twitter/X Thread

```
🧵 1/6 I built a $0/month LLM router that connects 11 provider integrations
    with automatic fallback. Here's how it works:

🧵 2/6 Instead of relying on ONE API key, the router chains
    6 providers per task type. If one fails → next one takes over instantly.

🧵 3/6 Task detection is keyword-based. "Write Python code" →
    CODE chain (Kimi K2 → Qwen3 Coder → Mimo Pro → ...)

🧵 4/6 Semantic cache at 0.82 threshold means repeated/similar prompts
    can return without hitting another API.

🧵 5/6 SMART_KEY detection: paste any API key and the router
    auto-detects the provider from the prefix. Zero config.

🧵 6/6 Fully open source. MCP-compatible. Works with Claude Code,
    Cursor, Windsurf, Codex CLI, and any MCP client.
    
    github.com/m4stanuj/mast-llm-router
    
    #LLM #AI #OpenSource #MCP
```

---

## LinkedIn Post

```
🏗️ Building a Fault-Tolerant LLM Router on Zero Budget

Most AI developers hit the same wall: rate limits, service outages, and
the constant need to switch between providers.

I spent the last few weeks building a solution:

MAST LLM Router — a task-aware fallback router that:
• Distributes requests across 11 provider integrations
• Auto-detects API keys from their prefix
• Falls through 6 models per chain on failure
• Caches semantically similar prompts (0.82 threshold)
• Costs exactly $0/month (free tiers only)

The architecture:
→ MCP Client → Task Detection → Chain Selection → Fallback Loop → Response

It runs as an MCP server, compatible with Claude Code, Cursor,
Windsurf, Continue.dev, and Codex CLI.

Stack: Python, FastMCP, free-tier LLM APIs

GitHub: https://github.com/m4stanuj/mast-llm-router

Hashtags:
#ArtificialIntelligence #MachineLearning #OpenSource
#Python #LLM #AIDevelopment #DevTools
```

---

## GitHub Trending Caption

```
🔥 MAST LLM Router — #1 Free-Tier LLM Router

✨ Features:
• 11 provider integrations • 10 task chains • 6 fallbacks per chain
• Semantic caching • Auto key detection • $0/month
• MCP native • Docker-ready • fallback-first routing

👇 Star on GitHub
```

---

## Reddit / HackerNews Post

```
Show HN: I built a free LLM router with 11 provider integrations and automatic failover

I got tired of hitting rate limits on individual providers, so I built a
task-aware router that chains 6 providers per task type. If one fails,
the next takes over automatically.

It costs $0/month — runs entirely on free-tier API quotas.

Key features:
• 11 provider integrations (Groq, Cerebras, Gemini, DeepSeek, OpenRouter, etc.)
• 10 task chains (code, reason, speed, vision, hinglish, etc.)
• SMART_KEY detection — paste any API key, provider auto-detected
• Fuzzy semantic cache at 0.82 threshold
• Dual transport: stdio (local) + HTTP (remote)
• MCP compatible — works with Claude Code, Cursor, Codex

GitHub: https://github.com/m4stanuj/mast-llm-router

Happy to answer questions!
```

---

## Hashtag Collections

### General
```
#LLM #AI #OpenSource #MCP #Python #MachineLearning
#DeveloperTools #AIAgents #LLMRouter #FreeAPI
#ArtificialIntelligence #ML #DeepLearning
```

### Technical
```
#Python #FastAPI #MCP #SemanticCache #LLM #API
#Backend #DevOps #Serverless #EdgeComputing
#ModelRouter #FallbackArchitecture
```

### Product Hunt / Launch
```
#ProductHunt #Launch #IndieHacker #OpenSource
#Developer #AITools #Tech #SaaS #SideProject
```

---

## Demo Video Script (30s)

```
[0:00] Open terminal — "python src/server.py"
[0:05] Server starts — "MCP server running on stdio"
[0:08] Claude Code connects — "claude mcp add mast-router..."
[0:12] Prompt: "Write a Python scraper for Hacker News"
[0:16] Router detects → CODE chain → Kimi K2 → ✅ 1.2s
[0:20] Prompt: "yeh kya hai samjhao"
[0:24] Router detects → HINGLISH chain → NVIDIA/Sarvam-M → ✅
[0:28] "llm_router_status" shows provider health + fallback chains
[0:30] End — "github.com/m4stanuj/mast-llm-router"
```

---

*Built by @m4stanuj · Share freely with attribution*
