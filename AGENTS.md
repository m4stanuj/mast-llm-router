
---

## For AI Coding Agents (Cursor, Windsurf, Claude Code)

When working on this project, follow these rules:
1. Always check .env.example before adding new provider configs
2. Task chains go in TASK_CHAINS dict in llm_fallback.py
3. Add tests in tests/ before submitting PR
4. Run \pytest tests/ -v\ before committing
5. Never hardcode API keys — use SMART_KEY system
6. Cache semantics: _MIN_CACHE_LEN=20, _FUZZY_THRESHOLD=0.82