# M4ST Model Router

Task-aware model routing and fallback layer by Mast Anuj.

This module helps M4ST choose a useful model path for each task, recover when providers fail, and keep repeated work cheaper through prompt reuse.

## What It Does

- Detects task type from the request.
- Selects a free/local-first model route.
- Falls back when a route rate-limits, errors, or returns an empty response.
- Reuses similar prior prompts when safe.
- Exposes routing tools through MCP-compatible workflows.
- Keeps provider details configurable through environment variables.

## Core Loop

```text
prompt -> task detection -> route selection -> fallback loop -> response -> usage log
```

## Use Cases

| Use case | Behavior |
|---|---|
| Fast answers | Pick a low-latency route first |
| Coding | Prefer code-capable routes |
| Research | Prefer reasoning and source-aware routes |
| Writing | Prefer stable writing routes |
| Hinglish | Prefer models that handle mixed Hindi-English well |
| Sensitive/local work | Prefer local/offline fallback where configured |

## Install

```bash
git clone https://github.com/m4stanuj/mast-llm-router.git
cd mast-llm-router
pip install -r requirements.txt
```

Configure keys locally through `.env`. Do not commit API keys, tokens, passwords, or private account data.

## MCP Usage

Point your MCP-compatible client at the server entrypoint:

```bash
python src/server.py
```

## M4ST Fit

This router is part of the M4ST local-first operator stack:

- M4ST local AI operator
- M4ST MCP workspace
- M4ST prompt reuse cache
- LeadSniper workflows
- authorized defensive OSINT workflows

## Safety Boundary

This project is routing infrastructure. It does not bypass provider limits, scrape private data, or move secrets into new services.

Use local configuration, keep secrets out of Git, and verify the selected route before using it for sensitive work.
