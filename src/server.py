"""
MAST LLM Router — MCP Server v6.0
===================================
Wraps llm_fallback.py as a fully-featured MCP server.
Compatible with: Claude Code, Codex CLI, Cursor, Windsurf,
                 Continue.dev, Antigravity, Magnus, and any
                 MCP-compatible client.

Transport: stdio (default) | streamable HTTP (--http flag)
"""

import sys
import json
import logging
import os
import asyncio
import time
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("mast_router_mcp")

# ── Import core router ────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import llm_fallback as router
except ImportError as e:
    log.error(f"Failed to import llm_fallback: {e}")
    sys.exit(1)

# ── FastMCP init ──────────────────────────────────────────────────────
mcp = FastMCP(
    "mast_router_mcp",
    instructions=(
        "MAST LLM Router: routes your prompt to the best free-tier AI model "
        "based on task type. Supports 11 providers, 10 task chains, semantic "
        "cache, and automatic fallback. Zero monthly cost. "
        "Use llm_detect_task to preview routing. "
        "Use llm_batch for parallel multi-prompt workflows. "
        "Use llm_stream for long-form generation with progress updates."
    ),
)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

VALID_TASKS = [
    "auto", "speed", "reason", "code", "vision",
    "research", "write", "agent", "vision_reason",
    "pentest", "hinglish",
]

# ═══════════════════════════════════════════════════════════════
# INPUT MODELS
# ═══════════════════════════════════════════════════════════════

class ChatInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    prompt: str = Field(
        ...,
        description="The user message / prompt to send to the LLM.",
        min_length=1,
        max_length=32000,
    )
    task: str = Field(
        default="auto",
        description=(
            "Routing hint. One of: auto, speed, reason, code, vision, "
            "research, write, agent, vision_reason, pentest, hinglish. "
            "'auto' detects task from prompt keywords automatically."
        ),
    )
    system: Optional[str] = Field(
        default=None,
        description="Optional system prompt / persona to prepend.",
        max_length=8000,
    )
    max_tokens: int = Field(default=1024, description="Maximum tokens.", ge=64, le=8192)
    use_cache: bool = Field(default=True, description="Use semantic cache.")


class MultiTurnInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    messages: list = Field(
        ...,
        description=(
            'Full conversation history as [{"role": "user"|"assistant"|"system", '
            '"content": "..."}]. Last message must be role=user.'
        ),
        min_length=1,
    )
    task: str = Field(default="auto", description="Task routing hint.")
    max_tokens: int = Field(default=1024, ge=64, le=8192)
    use_cache: bool = Field(default=False)


class StatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verbose: bool = Field(
        default=False,
        description="Show per-provider key counts and cooldown details.",
    )


class CacheInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(..., description="'stats' to view info | 'clear' to wipe cache.")


class DetectTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    prompt: str = Field(
        ...,
        description="Prompt text to analyze for task type detection.",
        min_length=1,
        max_length=4000,
    )


class StreamInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    prompt: str = Field(
        ...,
        description="The prompt to stream a response for.",
        min_length=1,
        max_length=32000,
    )
    task: str = Field(default="auto", description="Task routing hint.")
    system: Optional[str] = Field(default=None, max_length=8000)
    max_tokens: int = Field(default=2048, ge=64, le=8192)
    chunk_size: int = Field(
        default=40,
        description="Approximate characters per progress update chunk.",
        ge=10,
        le=500,
    )


class BatchPromptItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        description="Unique identifier for this prompt (returned in results).",
        min_length=1,
        max_length=64,
    )
    prompt: str = Field(..., min_length=1, max_length=32000)
    task: str = Field(default="auto")
    max_tokens: int = Field(default=512, ge=64, le=4096)


class BatchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompts: List[BatchPromptItem] = Field(
        ...,
        description="List of prompts to process. Each needs a unique 'id'.",
        min_length=1,
        max_length=20,
    )
    concurrency: int = Field(
        default=3,
        description="Max parallel requests (1-5).",
        ge=1,
        le=5,
    )
    stop_on_error: bool = Field(
        default=False,
        description="Stop entire batch on first error.",
    )


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _validate_task(task: str) -> Optional[str]:
    """Return error string if task invalid, else None."""
    if task not in VALID_TASKS:
        return f"ERROR: Invalid task '{task}'. Valid: {', '.join(VALID_TASKS)}"
    return None


def _validate_messages(messages: list) -> Optional[str]:
    """Return error string if messages malformed, else None."""
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return f"ERROR: Message {i} must be a dict."
        if "role" not in msg or "content" not in msg:
            return f"ERROR: Message {i} missing 'role' or 'content'."
        if msg["role"] not in ("user", "assistant", "system"):
            return f"ERROR: Message {i} has invalid role '{msg['role']}'."
    return None


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_chat
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_chat",
    annotations={
        "title": "Chat with MAST LLM Router",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def llm_chat(params: ChatInput) -> str:
    """Route a single-turn prompt to the best available free LLM.

    Automatically selects optimal model chain based on task type.
    Falls back through 6 models per chain before giving up.
    Supports semantic caching to avoid repeat API calls.

    Args:
        params (ChatInput):
            - prompt (str): The user's message.
            - task (str): Routing hint (default: 'auto').
            - system (Optional[str]): System prompt.
            - max_tokens (int): Max response length (default: 1024).
            - use_cache (bool): Enable cache (default: True).

    Returns:
        str: The LLM response text, or error string prefixed with 'ERROR:'.
    """
    err = _validate_task(params.task)
    if err:
        return err

    messages = []
    if params.system:
        messages.append({"role": "system", "content": params.system})
    messages.append({"role": "user", "content": params.prompt})

    try:
        return router.chat_complete(
            messages=messages,
            max_tokens=params.max_tokens,
            use_cache=params.use_cache,
            task=params.task,
        )
    except Exception as e:
        log.error(f"llm_chat error: {e}")
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_chat_multi_turn
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_chat_multi_turn",
    annotations={
        "title": "Multi-Turn Chat",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def llm_chat_multi_turn(params: MultiTurnInput) -> str:
    """Send a full conversation history to the LLM router.

    Use for multi-turn conversations where prior context matters.
    Pass the complete message history each time — router is stateless.

    Args:
        params (MultiTurnInput):
            - messages (list): Full conversation as role/content dicts.
            - task (str): Routing hint (default: 'auto').
            - max_tokens (int): Max response length.
            - use_cache (bool): Cache lookup (default: False).

    Returns:
        str: The LLM response text.

    Example messages:
        [
          {"role": "system", "content": "You are a security researcher."},
          {"role": "user", "content": "What is SQL injection?"},
          {"role": "assistant", "content": "SQL injection is..."},
          {"role": "user", "content": "Show me a detection query."}
        ]
    """
    err = _validate_task(params.task) or _validate_messages(params.messages)
    if err:
        return err

    try:
        return router.chat_complete(
            messages=params.messages,
            max_tokens=params.max_tokens,
            use_cache=params.use_cache,
            task=params.task,
        )
    except Exception as e:
        log.error(f"llm_chat_multi_turn error: {e}")
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_stream
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_stream",
    annotations={
        "title": "Streaming LLM Response",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def llm_stream(params: StreamInput, ctx: Context) -> str:
    """Stream a long-form LLM response with real-time progress updates.

    Best for: long code generation, essays, detailed analysis, reports.
    Reports progress in chunks so client sees incremental output.
    Auto-falls back to non-streaming if provider doesn't support SSE.

    Args:
        params (StreamInput):
            - prompt (str): The user's message.
            - task (str): Routing hint (default: 'auto').
            - system (Optional[str]): System prompt.
            - max_tokens (int): Max tokens (default: 2048).
            - chunk_size (int): Chars per progress update (default: 40).

    Returns:
        str: Full assembled response text.
    """
    err = _validate_task(params.task)
    if err:
        return err

    messages = []
    if params.system:
        messages.append({"role": "system", "content": params.system})
    messages.append({"role": "user", "content": params.prompt})

    await ctx.report_progress(0.05, f"Detecting task... ({params.task})")

    actual_task = params.task if params.task != "auto" else router._detect_task(messages)
    chain = router.TASK_CHAINS.get(actual_task, router.PROVIDERS)
    chain_names = [p["name"] for p in chain]

    await ctx.report_progress(0.10, f"Task: {actual_task} | Chain: {' → '.join(chain_names[:3])}...")

    now = time.time()
    full_text = ""
    streamed = False

    for provider in chain:
        with router._COOLDOWNS_LOCK:
            if router._cooldowns.get(provider["name"], 0) > now:
                continue

        key, _ = router._next_key(provider)
        if "PLACEHOLDER" in key:
            continue

        # Gemini uses a different API — skip for streaming
        if provider.get("type") == "gemini":
            continue

        try:
            import requests as req

            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            if "openrouter" in provider["name"]:
                headers["HTTP-Referer"] = "https://github.com/mast-anuj/mast-llm-router"
                headers["X-Title"] = "MAST Router"

            payload = {
                "model": provider["model"],
                "messages": messages,
                "max_tokens": params.max_tokens,
                "stream": True,
            }

            await ctx.report_progress(0.15, f"Streaming from {provider['name']}...")

            resp = req.post(
                f"{provider['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=60,
            )

            if resp.status_code != 200:
                log.warning(f"Stream {provider['name']} returned {resp.status_code}")
                continue

            chunk_buffer = ""
            chars_received = 0
            total_estimate = params.max_tokens * 3

            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8") if isinstance(line, bytes) else line
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    delta = json.loads(data)
                    content = (
                        delta.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    if content:
                        full_text += content
                        chunk_buffer += content
                        chars_received += len(content)
                        if len(chunk_buffer) >= params.chunk_size:
                            progress = min(
                                0.15 + (chars_received / max(total_estimate, 1)) * 0.80,
                                0.95,
                            )
                            await ctx.report_progress(progress, chunk_buffer)
                            chunk_buffer = ""
                            await asyncio.sleep(0)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

            if chunk_buffer:
                await ctx.report_progress(0.97, chunk_buffer)

            streamed = True
            break

        except Exception as e:
            log.warning(f"Stream failed for {provider['name']}: {e}")
            continue

    # Fallback to non-streaming
    if not streamed or not full_text:
        await ctx.report_progress(0.20, "Streaming unavailable — using standard call...")
        try:
            full_text = router.chat_complete(
                messages=messages,
                max_tokens=params.max_tokens,
                use_cache=False,
                task=params.task,
            )
        except Exception as e:
            return f"ERROR: {e}"

    await ctx.report_progress(1.0, "Complete.")
    return full_text


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_batch
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_batch",
    annotations={
        "title": "Batch LLM Requests",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def llm_batch(params: BatchInput, ctx: Context) -> str:
    """Process multiple prompts concurrently through the LLM router.

    Ideal for: bulk code review, parallel analysis, multi-doc summarization,
    generating variations, or any agent workflow needing many LLM calls.
    Uses asyncio.Semaphore to respect concurrency limits.

    Args:
        params (BatchInput):
            - prompts (list): Up to 20 BatchPromptItem objects, each with:
                - id (str): Unique identifier for tracking results.
                - prompt (str): The prompt text.
                - task (str): Per-prompt task routing (default: 'auto').
                - max_tokens (int): Per-prompt token limit (default: 512).
            - concurrency (int): Parallel requests 1-5 (default: 3).
            - stop_on_error (bool): Abort on first failure (default: False).

    Returns:
        str: JSON with summary stats and per-prompt results.

    Schema:
        {
          "summary": {"total": int, "ok": int, "errors": int, "total_ms": int, "avg_ms": int},
          "results": [{"id": str, "status": "ok"|"error", "response": str,
                       "task": str, "duration_ms": int}]
        }
    """
    semaphore = asyncio.Semaphore(params.concurrency)
    completed = 0
    total = len(params.prompts)

    await ctx.report_progress(0.0, f"Batch start: {total} prompts | concurrency={params.concurrency}")

    async def process_one(item: BatchPromptItem) -> dict:
        nonlocal completed
        async with semaphore:
            start = time.time()
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: router.chat_complete(
                        messages=[{"role": "user", "content": item.prompt}],
                        max_tokens=item.max_tokens,
                        use_cache=True,
                        task=item.task,
                    ),
                )
                duration = int((time.time() - start) * 1000)
                completed += 1
                await ctx.report_progress(
                    completed / total,
                    f"[{completed}/{total}] '{item.id}' ✓ {duration}ms",
                )
                return {
                    "id": item.id,
                    "status": "ok",
                    "response": response,
                    "task": item.task,
                    "duration_ms": duration,
                }
            except Exception as e:
                duration = int((time.time() - start) * 1000)
                completed += 1
                log.error(f"Batch '{item.id}' failed: {e}")
                return {
                    "id": item.id,
                    "status": "error",
                    "response": f"ERROR: {e}",
                    "task": item.task,
                    "duration_ms": duration,
                }

    results = []
    if params.stop_on_error:
        for item in params.prompts:
            result = await process_one(item)
            results.append(result)
            if result["status"] == "error":
                await ctx.report_progress(1.0, f"Stopped at '{item.id}' — error.")
                break
    else:
        results = list(await asyncio.gather(*[process_one(item) for item in params.prompts]))

    ok_count = sum(1 for r in results if r["status"] == "ok")
    total_ms = sum(r["duration_ms"] for r in results)

    await ctx.report_progress(1.0, f"Done: {ok_count}/{len(results)} ok")
    return json.dumps(
        {
            "summary": {
                "total": len(results),
                "ok": ok_count,
                "errors": len(results) - ok_count,
                "total_ms": total_ms,
                "avg_ms": total_ms // max(len(results), 1),
            },
            "results": results,
        },
        indent=2,
        ensure_ascii=False,
    )


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_router_status
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_router_status",
    annotations={
        "title": "Router Status Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def llm_router_status(params: StatusInput) -> str:
    """Get current status of all LLM providers and task chains.

    Shows which providers are active, cooled-down, or missing keys.
    Also displays cache statistics and available task chains.

    Args:
        params (StatusInput):
            - verbose (bool): Show per-key cooldown details (default: False).

    Returns:
        str: Formatted status report with provider health and cache stats.
    """
    try:
        return router.status_report()
    except Exception as e:
        return f"ERROR fetching status: {e}"


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_detect_task
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_detect_task",
    annotations={
        "title": "Detect Task Type from Prompt",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def llm_detect_task(params: DetectTaskInput) -> str:
    """Detect which task chain would be selected for a given prompt.

    Use to debug routing decisions or preview which models will handle
    a request before actually sending it.

    Args:
        params (DetectTaskInput):
            - prompt (str): Text to analyze.

    Returns:
        str: JSON with detected task, matched keywords, and model chain.

    Example return:
        {
          "detected_task": "code",
          "chain": ["kimi-k2", "qwen3-coder", "mimo-pro", ...],
          "chain_length": 6,
          "matched_keywords": ["script", "python"],
          "all_tasks": [...]
        }
    """
    try:
        messages = [{"role": "user", "content": params.prompt}]
        task = router._detect_task(messages)
        chain = router.TASK_CHAINS.get(task, router.PROVIDERS)
        chain_names = [p["name"] for p in chain]

        text = params.prompt.lower()
        matched = [
            kw for kw in router._TASK_KEYWORDS.get(task, [])
            if kw in text
        ][:5]

        return json.dumps(
            {
                "detected_task": task,
                "chain": chain_names,
                "chain_length": len(chain_names),
                "matched_keywords": matched,
                "all_tasks": list(router.TASK_CHAINS.keys()),
            },
            indent=2,
        )
    except Exception as e:
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_cache_control
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_cache_control",
    annotations={
        "title": "Cache Stats / Clear",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def llm_cache_control(params: CacheInput) -> str:
    """View cache statistics or clear the semantic response cache.

    The router uses a semantic cache with fuzzy matching (0.82 threshold)
    to avoid redundant API calls for similar prompts.

    Args:
        params (CacheInput):
            - action (str): 'stats' to view | 'clear' to wipe.

    Returns:
        str: Cache stats or confirmation message.
    """
    if params.action == "stats":
        try:
            return router.cache_stats()
        except Exception as e:
            return f"ERROR: {e}"
    elif params.action == "clear":
        try:
            router._cache.clear()
            router._save_cache_bg()
            return "Cache cleared successfully."
        except Exception as e:
            return f"ERROR clearing cache: {e}"
    else:
        return "ERROR: Invalid action. Use 'stats' or 'clear'."


# ═══════════════════════════════════════════════════════════════
# TOOL: llm_list_providers
# ═══════════════════════════════════════════════════════════════

@mcp.tool(
    name="llm_list_providers",
    annotations={
        "title": "List All Providers and Chains",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def llm_list_providers(params: StatusInput) -> str:
    """List all available providers, models, and task chains.

    Args:
        params (StatusInput):
            - verbose (bool): Include base URLs and key counts (default: False).

    Returns:
        str: JSON with providers list and task chain definitions.

    Schema:
        {
          "providers": [{"name": str, "model": str, "keys_loaded": bool}],
          "task_chains": {"task_name": ["provider1", ...]},
          "total_providers": int,
          "total_chains": int,
          "valid_task_values": [...]
        }
    """
    try:
        providers = []
        for p in router.PROVIDERS:
            entry = {
                "name": p["name"],
                "model": p["model"],
                "keys_loaded": any("PLACEHOLDER" not in k for k in p["keys"]),
            }
            if params.verbose:
                entry["base_url"] = p.get("base_url", "gemini-native")
                entry["key_count"] = len(p["keys"])
            providers.append(entry)

        chains = {
            task: [p["name"] for p in chain]
            for task, chain in router.TASK_CHAINS.items()
        }

        return json.dumps(
            {
                "providers": providers,
                "task_chains": chains,
                "total_providers": len(providers),
                "total_chains": len(chains),
                "valid_task_values": VALID_TASKS,
            },
            indent=2,
        )
    except Exception as e:
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    """Entry point for `mast-router` CLI (defined in pyproject.toml scripts)."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="mast-router",
        description="MAST LLM Router — MCP Server v6.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mast-router                      # stdio mode (Claude Code, Codex, Cursor)
  mast-router --http               # HTTP mode on port 8000
  mast-router --http --port 9000   # HTTP mode custom port
  python src/server.py             # direct run
        """,
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP server instead of stdio",
    )
    parser.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    parser.add_argument("--version", action="version", version="mast-llm-router 6.0.0")
    args = parser.parse_args()

    if args.http:
        log.warning(f"Starting HTTP transport on port {args.port}")
        mcp.run(transport="streamable_http", port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
