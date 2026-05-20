"""Tests for run_dimension_generator using a mocked cost_tracker."""
import json
import pytest

from poc2_research_agent.agents.dimension_generator import run_dimension_generator, DimensionGenerationError
from poc2_research_agent.agents.goal_setter import run_goal_setter
from poc2_research_agent.memory.working_memory import WorkingMemory


class DummyCostTracker:
    def __init__(self, scenario, response_text=None, raise_on_call=False):
        self.scenario = scenario
        self._response_text = response_text
        self._raise = raise_on_call

    def call_llm(self, component, model, messages, system=None, max_tokens=1000):
        if self._raise:
            raise RuntimeError("llm fail")
        return self._response_text


def make_response(questions):
    return json.dumps(questions)


def test_1_valid_goal_memory_generates_6_dimensions():
    gm = run_goal_setter("Reliance Industries")
    questions = [f"Question {i}" for i in range(1, 7)]
    ct = DummyCostTracker("S-A", response_text=make_response(questions))
    wm = run_dimension_generator(gm, ct)
    assert isinstance(wm, WorkingMemory)
    assert len(wm.dimensions) == 6


def test_2_all_dimensions_unanswered():
    gm = run_goal_setter("Reliance Industries")
    questions = [f"Q{i}" for i in range(6)]
    ct = DummyCostTracker("S-A", response_text=make_response(questions))
    wm = run_dimension_generator(gm, ct)
    assert all(d.status == "unanswered" for d in wm.dimensions)


def test_3_d6_contains_thesis_keywords():
    gm = run_goal_setter("Reliance Industries")
    questions = ["What is X?", "What is Y?", "A?", "B?", "C?", "What is the investment thesis (bull and bear case)?"]
    ct = DummyCostTracker("S-A", response_text=make_response(questions))
    wm = run_dimension_generator(gm, ct)
    assert "investment thesis" in wm.get_dimension("D6").question.lower()


def test_4_unlocked_goal_memory_raises():
    # create GoalMemory but do not lock
    from poc2_research_agent.memory.goal_memory import GoalMemory

    gm = GoalMemory(company="Example", purpose="p", scope="s", constraints="c", time_horizon="t")
    ct = DummyCostTracker("S-A", response_text=make_response(["a"] * 6))
    with pytest.raises(DimensionGenerationError):
        run_dimension_generator(gm, ct)


def test_5_llm_failure_raises_dimension_generation_error():
    gm = run_goal_setter("Reliance Industries")
    ct = DummyCostTracker("S-A", raise_on_call=True)
    with pytest.raises(DimensionGenerationError):
        run_dimension_generator(gm, ct)


def test_6_unique_ids():
    gm = run_goal_setter("Reliance Industries")
    questions = [f"Q{i}" for i in range(6)]
    ct = DummyCostTracker("S-A", response_text=make_response(questions))
    wm = run_dimension_generator(gm, ct)
    ids = [d.id for d in wm.dimensions]
    assert len(set(ids)) == len(ids)


def test_7_questions_non_empty_strings():
    gm = run_goal_setter("Reliance Industries")
    questions = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
    ct = DummyCostTracker("S-A", response_text=make_response(questions))
    wm = run_dimension_generator(gm, ct)
    assert all(isinstance(d.question, str) and d.question.strip() for d in wm.dimensions)
"""Placeholder test file for dimension_generator."""

# No tests yet.
