"""Tests for CostTracker. Mocks Anthropic and OpenAI SDKs to simulate responses."""
import json
import os
import types
import pytest

from poc2_research_agent.tracking.cost_tracker import CostTracker, LLMCallError


class DummyAnthropicClient:
    def __init__(self, response_text="anth_resp", out_tokens=50):
        self._response_text = response_text
        self._out_tokens = out_tokens

    def create(self, **kwargs):
        return {"text": self._response_text, "output_tokens": self._out_tokens}


class DummyOpenAIClient:
    def __init__(self, response_text="openai_resp", out_tokens=30):
        self._response_text = response_text
        self._out_tokens = out_tokens

    def create(self, **kwargs):
        return {"text": self._response_text, "output_tokens": self._out_tokens}


def test_1_call_llm_anthropic_returns_and_logs(monkeypatch, tmp_path):
    # Mock anthropic module
    anthropic_mod = types.SimpleNamespace(Anthropic=lambda: DummyAnthropicClient("hello anth", 60))
    monkeypatch.setitem(__import__("sys").modules, "anthropic", anthropic_mod)

    log_path = str(tmp_path / "cost_log.json")
    ct = CostTracker(scenario="S-A", company="Acme", log_path=log_path)
    resp = ct.call_llm(component="C2", model="claude-sonnet-4-6", messages=[{"role":"user","content":"hi"}])
    assert resp == "hello anth"
    assert len(ct.session_calls) == 1


def test_2_call_llm_openai_returns_and_logs(monkeypatch, tmp_path):
    openai_mod = types.SimpleNamespace(OpenAI=lambda: DummyOpenAIClient("hi openai", 40))
    monkeypatch.setitem(__import__("sys").modules, "openai", openai_mod)

    log_path = str(tmp_path / "cost_log.json")
    ct = CostTracker(scenario="S-B", company="Beta", log_path=log_path)
    resp = ct.call_llm(component="C3", model="gpt-4o", messages=[{"role":"user","content":"q"}])
    assert resp == "hi openai"
    assert len(ct.session_calls) == 1


def test_3_calculate_cost_claude_sonnet():
    ct = CostTracker("S-A", "C")
    cost = ct._calculate_cost("claude-sonnet-4-6", input_tokens=1000, output_tokens=2000)
    # cost = (1000/1e6)*3 + (2000/1e6)*15 = 0.003 + 0.03 = 0.033
    assert abs(cost - 0.033) < 1e-9


def test_4_calculate_cost_gpt4o_mini():
    ct = CostTracker("S-A", "C")
    cost = ct._calculate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=2000)
    # cost = (1000/1e6)*0.15 + (2000/1e6)*0.6 = 0.00015 + 0.0012 = 0.00135
    assert abs(cost - 0.00135) < 1e-9


def test_5_write_to_log_appends(tmp_path):
    log_path = str(tmp_path / "cost_log.json")
    ct = CostTracker("S-A", "C", log_path=log_path)
    entry = {"a": 1}
    ct._write_to_log(entry)
    with open(log_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data[-1]["a"] == 1


def test_6_write_to_log_file_error_is_silent(monkeypatch, tmp_path, capsys):
    # Force open to throw when writing
    log_path = str(tmp_path / "cost_log.json")
    ct = CostTracker("S-A", "C", log_path=log_path)

    def fake_open(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", fake_open)
    # Should not raise
    ct._write_to_log({"x": 1})
    captured = capsys.readouterr()
    assert "Warning: failed to write cost log" in captured.out


def test_7_get_session_summary_totals(monkeypatch):
    anthropic_mod = types.SimpleNamespace(Anthropic=lambda: DummyAnthropicClient("r1", 10))
    openai_mod = types.SimpleNamespace(OpenAI=lambda: DummyOpenAIClient("r2", 20))
    monkeypatch.setitem(__import__("sys").modules, "anthropic", anthropic_mod)
    monkeypatch.setitem(__import__("sys").modules, "openai", openai_mod)

    ct = CostTracker("S-X", "Co")
    ct.call_llm("C2", "claude-sonnet-4-6", [{"r":"u"}])
    ct.call_llm("C3", "gpt-4o", [{"r":"u"}])
    summary = ct.get_session_summary()
    assert summary["scenario"] == "S-X"
    assert summary["company"] == "Co"
    assert summary["total_input_tokens"] > 0
    assert summary["total_output_tokens"] > 0
    assert "C2" in summary["calls_by_component"]


def test_8_llm_api_failure_is_logged_and_raises(monkeypatch, tmp_path):
    class FailingClient:
        def create(self, **kwargs):
            raise RuntimeError("api down")

    anthropic_mod = types.SimpleNamespace(Anthropic=lambda: FailingClient())
    monkeypatch.setitem(__import__("sys").modules, "anthropic", anthropic_mod)

    log_path = str(tmp_path / "cost_log.json")
    ct = CostTracker("S-ERR", "ErrCo", log_path=log_path)
    with pytest.raises(LLMCallError):
        ct.call_llm("C2", "claude-sonnet-4-6", [{"r":"u"}])
    # Ensure failure entry was appended (session_calls contains 1 entry)
    assert len(ct.session_calls) == 1
    assert "error" in ct.session_calls[0]
"""Placeholder test file for cost_tracker."""

# No tests yet.
