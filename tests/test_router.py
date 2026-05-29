"""
MAST LLM Router — Unit Tests
Runs without real API keys.
"""

import sys
import os
import types
import pytest

# ── Stub external deps before import ────────────────────────────────
for mod in ["requests", "langchain_openai", "langchain_google_genai"]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import llm_fallback as router


# ═══════════════════════════════════════
# Task detection
# ═══════════════════════════════════════

class TestTaskDetection:
    def _msg(self, text):
        return [{"role": "user", "content": text}]

    def test_code_detection(self):
        result = router._detect_task(self._msg("write a python script to sort a list"))
        assert result == "code"

    def test_pentest_detection(self):
        result = router._detect_task(self._msg("run nmap scan on this target network"))
        assert result == "pentest"

    def test_hinglish_detection(self):
        result = router._detect_task(self._msg("bhai mujhe batao yeh kya hai hinglish mein"))
        assert result == "hinglish"

    def test_speed_detection(self):
        result = router._detect_task(self._msg("quick answer: capital of France"))
        assert result == "speed"

    def test_reason_detection(self):
        result = router._detect_task(self._msg("analyze and reason through this logic puzzle step by step"))
        assert result == "reason"

    def test_returns_valid_task(self):
        """Any prompt must return a task that exists in TASK_CHAINS."""
        for prompt in ["hello", "???", "   ", "1+1"]:
            result = router._detect_task([{"role": "user", "content": prompt}])
            assert result in router.TASK_CHAINS, f"Unknown task '{result}' for prompt '{prompt}'"

    def test_all_chains_non_empty(self):
        for task, chain in router.TASK_CHAINS.items():
            assert len(chain) > 0, f"Empty chain for task: {task}"

    def test_all_chain_providers_have_required_fields(self):
        for task, chain in router.TASK_CHAINS.items():
            for p in chain:
                assert "name" in p, f"Chain '{task}' provider missing 'name'"
                assert "model" in p, f"Chain '{task}' provider missing 'model'"
                assert "type" in p, f"Chain '{task}' provider missing 'type'"


# ═══════════════════════════════════════
# Provider structure
# ═══════════════════════════════════════

class TestProviderStructure:
    def test_minimum_provider_count(self):
        assert len(router.PROVIDERS) >= 10, f"Expected 10+ providers, got {len(router.PROVIDERS)}"

    def test_required_fields(self):
        required = {"name", "model", "keys", "type"}
        for p in router.PROVIDERS:
            missing = required - set(p.keys())
            assert not missing, f"Provider '{p.get('name')}' missing: {missing}"

    def test_keys_is_list(self):
        for p in router.PROVIDERS:
            assert isinstance(p["keys"], list), f"'{p['name']}' keys must be list"
            assert len(p["keys"]) >= 1, f"'{p['name']}' has empty keys list"

    def test_valid_types(self):
        valid = {"openai_compat", "gemini"}
        for p in router.PROVIDERS:
            assert p["type"] in valid, f"'{p['name']}' has invalid type: {p['type']}"

    def test_openai_compat_has_base_url(self):
        for p in router.PROVIDERS:
            if p["type"] == "openai_compat":
                assert "base_url" in p, f"'{p['name']}' missing base_url"
                assert p["base_url"].startswith("http"), f"'{p['name']}' bad base_url: {p['base_url']}"

    def test_no_duplicate_provider_names(self):
        names = [p["name"] for p in router.PROVIDERS]
        assert len(names) == len(set(names)), f"Duplicate provider names: {names}"


# ═══════════════════════════════════════
# Smart key detection
# ═══════════════════════════════════════

class TestSmartKeyDetection:
    """Test SMART_KEY auto-detection via environment variables."""

    def _inject_and_load(self, key: str) -> dict:
        """Inject a key as SMART_KEY_1 and reload smart key map."""
        os.environ["SMART_KEY_1"] = key
        result = router._load_smart_keys()
        del os.environ["SMART_KEY_1"]
        return result

    def test_groq_prefix(self):
        smart = self._inject_and_load("gsk_" + "a" * 40)
        assert "GROQ" in smart

    def test_cerebras_prefix(self):
        smart = self._inject_and_load("csk-" + "a" * 40)
        assert "CEREBRAS" in smart

    def test_gemini_prefix(self):
        smart = self._inject_and_load("AIzaSy" + "a" * 33)
        assert "GEMINI" in smart

    def test_openrouter_prefix(self):
        smart = self._inject_and_load("sk-or-v1-" + "a" * 60)
        assert "OPENROUTER" in smart

    def test_nvidia_prefix(self):
        smart = self._inject_and_load("nvapi-" + "a" * 80)
        assert "NVIDIA" in smart

    def test_mistral_prefix(self):
        smart = self._inject_and_load("msk-" + "a" * 40)
        assert "MISTRAL" in smart

    def test_xai_prefix(self):
        smart = self._inject_and_load("xai-" + "a" * 50)
        assert "GROKAI" in smart

    def test_huggingface_prefix(self):
        smart = self._inject_and_load("hf_" + "a" * 30)
        assert "HUGGINGFACE" in smart

    def test_sambanova_uuid(self):
        smart = self._inject_and_load("550e8400-e29b-41d4-a716-446655440000")
        assert "SAMBANOVA" in smart

    def test_unknown_key_ignored(self):
        smart = self._inject_and_load("unknownrandomkey123")
        # Should not crash, may return empty or partial
        assert isinstance(smart, dict)


# ═══════════════════════════════════════
# Cache
# ═══════════════════════════════════════

class TestCache:
    def setup_method(self):
        router._cache.clear()

    def test_miss_returns_none(self):
        assert router.cache_get("totally_unique_prompt_xyz_99999") is None

    def test_set_and_exact_get(self):
        router.cache_set("what is python", "Python is a language")
        result = router.cache_get("what is python")
        assert result == "Python is a language"

    def test_different_prompt_no_hit(self):
        router.cache_set("what is python", "Python is a language")
        result = router.cache_get("what is javascript")
        assert result != "Python is a language"

    def test_cache_stats_is_string(self):
        stats = router.cache_stats()
        assert isinstance(stats, str) and len(stats) > 0

    def test_cache_stats_contains_numbers(self):
        router.cache_set("test key", "test value")
        stats = router.cache_stats()
        assert any(c.isdigit() for c in stats)


# ═══════════════════════════════════════
# Status report
# ═══════════════════════════════════════

class TestStatusReport:
    def test_runs_without_error(self):
        report = router.status_report()
        assert isinstance(report, str) and len(report) > 50

    def test_contains_mast(self):
        assert "MAST" in router.status_report()

    def test_contains_all_provider_names(self):
        report = router.status_report()
        for p in router.PROVIDERS:
            assert p["name"] in report, f"'{p['name']}' missing from status report"

    def test_contains_chains_line(self):
        assert "Chains:" in router.status_report()

    def test_contains_cache_stats(self):
        report = router.status_report()
        # cache_stats() output is embedded in status
        assert any(word in report.lower() for word in ["cache", "hit", "entries"])
