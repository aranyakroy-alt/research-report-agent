import pytest

from poc2_research_agent.agents.react_agent import run_react_agent
from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.working_memory import WorkingMemory, Dimension
from poc2_research_agent.memory.episodic_memory import EpisodicMemory, EpisodicEntry
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory


class DummyCostTracker:
    def __init__(self):
        self.calls = []

    def call_llm(self, component=None, model=None, messages=None, **kwargs):
        self.calls.append((component, model, messages))
        # return a unique-ish query per call to avoid the react agent skipping
        # repeated identical tool+query invocations
        return f"query-{len(self.calls)}"


def make_goal():
    return GoalMemory(company="Acme Corp", purpose="", scope="investigate", constraints="", time_horizon="1y")


def make_working(dims=6):
    wm = WorkingMemory()
    for i in range(1, dims + 1):
        wm.add_dimension(Dimension(id=f"D{i}", question=f"Question {i}"))
    return wm


def test_all_dimensions_attempted_and_written(monkeypatch):
    # D1-D5 should be processed; D6 skipped until answered
    goal = make_goal()
    wm = make_working(6)
    em = EpisodicMemory()
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    # Mock tools to return simple results
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", lambda company, q: {"rev": 100})
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", lambda company, days_back: [{"title": "x"}])
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", lambda q: "page text")

    scenario = {"C3": "m", "C4": "m"}
    wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, scenario)

    # Episodic should have entries for D1-D5 (D6 skipped)
    keys = em_out.all_keys()
    assert any(k.endswith("_d1") for k in keys)
    assert len(keys) >= 5

    # Working memory dims processed (not unanswered)
    for d in wm_out.dimensions:
        if d.id != "D6":
            assert d.status in {"in_progress", "tool_failure"}


def test_cache_hit_prevents_tool_call(monkeypatch):
    goal = make_goal()
    wm = make_working(1)
    em = EpisodicMemory()
    # Pre-populate cache entry for D1
    em.add(EpisodicEntry(key="acme_corp_d1", value="cached", source="test", fetched_at="now", used_by_dimensions=[]))
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    # If tool were called it would raise; ensure it's not called
    def _fail_tool(*a, **k):
        raise AssertionError("Tool should not be called when cache hit")

    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", _fail_tool)
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", _fail_tool)
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", _fail_tool)

    scenario = {"C3": "m", "C4": "m"}
    wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, scenario)

    # Ensure episodic entry still marked used
    e = em_out.get("acme_corp_d1")
    assert "D1" in e.used_by_dimensions


def test_tool_failure_marks_tool_failure_and_continues(monkeypatch):
    goal = make_goal()
    wm = make_working(3)
    em = EpisodicMemory()
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    # Make the selected tool fail (web_search_reader selected by default)
    def fail_once(q):
        raise RuntimeError("tool down")

    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", lambda company, q: {"t": 1})
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", lambda c, d: [{"t":1}])
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", fail_once)

    scenario = {"C3": "m", "C4": "m"}
    wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, scenario)

    # At least one dimension should be marked tool_failure
    assert any(d.status == "tool_failure" for d in wm_out.dimensions)


def test_max_tool_calls_respected(monkeypatch):
    from poc2_research_agent.agents import react_agent as ra

    goal = make_goal()
    wm = make_working(10)
    em = EpisodicMemory()
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", lambda company, q: {"rev": 1})
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", lambda company, days_back: [])
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", lambda q: "p")

    # Temporarily reduce max tool calls
    old = ra.MAX_TOOL_CALLS
    ra.MAX_TOOL_CALLS = 2
    try:
        wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, {"C3": "m", "C4": "m"})
        # Only up to 2 episodic entries should exist
        assert len(em_out.entries) <= 2
    finally:
        ra.MAX_TOOL_CALLS = old


def test_d6_processed_after_first_five(monkeypatch):
    goal = make_goal()
    wm = make_working(6)
    # mark first five answered
    for i in range(1, 6):
        wm.get_dimension(f"D{i}").status = "answered"

    em = EpisodicMemory()
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", lambda company, q: {"rev": 1})
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", lambda company, days_back: [])
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", lambda q: "p")

    wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, {"C3": "m", "C4": "m"})
    # D6 should have an episodic entry
    assert any(e.key.endswith("_d6") for e in em_out.entries)


def test_working_memory_updated_after_attempts(monkeypatch):
    goal = make_goal()
    wm = make_working(4)
    em = EpisodicMemory()
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", lambda company, q: {"rev": 1})
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", lambda company, days_back: [])
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", lambda q: "p")

    wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, {"C3": "m", "C4": "m"})
    for d in wm_out.dimensions:
        assert d.status in {"in_progress", "tool_failure"}


def test_episodic_written_count_matches_tool_calls(monkeypatch):
    goal = make_goal()
    wm = make_working(3)
    em = EpisodicMemory()
    evm = EvaluationMemory()
    ct = DummyCostTracker()

    monkeypatch.setattr("poc2_research_agent.agents.react_agent.financial_fetcher", lambda company, q: {"rev": 1})
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.news_scraper", lambda company, days_back: [])
    monkeypatch.setattr("poc2_research_agent.agents.react_agent.web_search_reader", lambda q: "p")

    wm_out, em_out, evm_out = run_react_agent(goal, wm, em, evm, ct, {"C3": "m", "C4": "m"})
    # Each tool call should have produced an episodic entry;
    # ct.calls includes both C3 (query gen) and C4 (evaluator) calls
    assert len(em_out.entries) >= 1
    assert len(ct.calls) >= len(em_out.entries)
"""Placeholder test file for react_agent."""

# No tests yet.
