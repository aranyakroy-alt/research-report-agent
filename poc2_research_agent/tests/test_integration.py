"""Integration tests – end-to-end pipeline (live LLM + tools).

These tests call real APIs; they are skipped automatically when any API key is
missing/placeholder. Run them explicitly:
    pytest poc2_research_agent/tests/test_integration.py -v
"""
import os
import json
import pathlib
import pytest

import poc2_research_agent.config as config
from poc2_research_agent.agents.goal_setter import GoalMemoryValidationError
from poc2_research_agent.main import run_agent

# ── helpers ──────────────────────────────────────────────────────────────────

REQUIRED_SECTIONS = [
    "business",       # Business Overview
    "financial",      # Key Financials / Financials
    "risk",           # Key Risks / Risk
    "thesis",         # Investment Thesis
    "sources",        # Sources
]

def _keys_ok():
    """True when all API keys are set to real values."""
    placeholders = {"", "your-key", "your key"}
    return (
        config.ANTHROPIC_API_KEY not in placeholders
        and config.OPENAI_API_KEY not in placeholders
        and config.NEWS_API_KEY not in placeholders
    )

needs_live_keys = pytest.mark.skipif(
    not _keys_ok(),
    reason="Live API keys not set – skipping integration tests",
)

# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def reliance_result():
    """Run the full S-A pipeline for Reliance Industries once; cache result."""
    return run_agent("Reliance Industries", "S-A")

@pytest.fixture(scope="module")
def infosys_result():
    """Run the full S-A pipeline for Infosys; separate brief expected."""
    return run_agent("Infosys", "S-A")

# ── tests ─────────────────────────────────────────────────────────────────────

@needs_live_keys
def test_1_reliance_brief_created(reliance_result):
    """run_agent returns a brief_path that exists on disk."""
    path = reliance_result["brief_path"]
    assert path, "brief_path must not be empty"
    assert pathlib.Path(path).exists(), f"Brief file not found: {path}"

@needs_live_keys
def test_2_infosys_brief_created_different_content(reliance_result, infosys_result):
    """Infosys brief is created and content differs from Reliance brief."""
    r_path = reliance_result["brief_path"]
    i_path = infosys_result["brief_path"]
    assert pathlib.Path(i_path).exists(), f"Infosys brief not found: {i_path}"
    r_text = pathlib.Path(r_path).read_text(encoding="utf-8")
    i_text = pathlib.Path(i_path).read_text(encoding="utf-8")
    assert r_text != i_text, "Briefs for different companies must differ"

def test_3_empty_company_raises():
    """Empty company name raises GoalMemoryValidationError cleanly."""
    with pytest.raises(GoalMemoryValidationError):
        run_agent("", "S-A")

@needs_live_keys
def test_4_all_sections_present(reliance_result):
    """Generated brief contains all 6 required section headings."""
    text = pathlib.Path(reliance_result["brief_path"]).read_text(encoding="utf-8").lower()
    for section in REQUIRED_SECTIONS:
        assert section.lower() in text, f"Missing section: {section}"

@needs_live_keys
def test_5_brief_word_count(reliance_result):
    """Brief must be ≤ 650 words (MAX_BRIEF_WORDS)."""
    text = pathlib.Path(reliance_result["brief_path"]).read_text(encoding="utf-8")
    word_count = len(text.split())
    assert word_count <= config.MAX_BRIEF_WORDS, (
        f"Brief too long: {word_count} words (limit {config.MAX_BRIEF_WORDS})"
    )

@needs_live_keys
def test_6_cost_summary_positive(reliance_result):
    """cost_summary must record total_cost_usd > 0 (real LLM was called)."""
    summary = reliance_result["cost_summary"]
    assert "total_cost_usd" in summary
    assert summary["total_cost_usd"] > 0, "No cost recorded – LLM may not have been called"

@needs_live_keys
def test_7_cost_log_written(reliance_result):
    """cost_log.json must exist under outputs/ after a run."""
    log_path = pathlib.Path(config.__file__).parent.parent / "outputs" / "cost_log.json"
    assert log_path.exists(), f"cost_log.json not found at {log_path}"
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) > 0, "cost_log.json is empty"
