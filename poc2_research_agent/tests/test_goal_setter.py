"""Tests for goal_setter.run_goal_setter"""
import pytest

from poc2_research_agent.agents.goal_setter import run_goal_setter
from poc2_research_agent.memory.goal_memory import GoalMemoryLockedError, GoalMemoryValidationError


def test_1_valid_company_returns_goal_memory():
    gm = run_goal_setter("Reliance Industries")
    assert gm.company == "Reliance Industries"


def test_2_whitespace_and_case_normalisation():
    gm = run_goal_setter("  reliance industries  ")
    assert gm.company == "Reliance Industries"


def test_3_empty_input_raises():
    with pytest.raises(GoalMemoryValidationError):
        run_goal_setter("")


def test_4_none_input_raises():
    with pytest.raises(GoalMemoryValidationError):
        run_goal_setter(None)


def test_5_returned_goal_memory_is_locked():
    gm = run_goal_setter("Example Co")
    assert gm.locked


def test_6_all_fields_populated():
    gm = run_goal_setter("Example Co")
    d = gm.to_dict()
    assert set(d.keys()) == {"company", "purpose", "scope", "constraints", "time_horizon"}


def test_7_update_after_lock_raises():
    gm = run_goal_setter("Example Co")
    with pytest.raises(GoalMemoryLockedError):
        gm.update("scope", "new scope")
"""Placeholder test file for goal_setter."""

# No tests yet.
