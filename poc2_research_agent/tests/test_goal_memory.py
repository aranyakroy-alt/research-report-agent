"""Tests for GoalMemory dataclass in memory/goal_memory.py"""
import pytest

from poc2_research_agent.memory.goal_memory import (
    GoalMemory,
    GoalMemoryLockedError,
    GoalMemoryValidationError,
)


def test_1_valid_input_creates_goal_memory():
    gm = GoalMemory(
        company="Example Co",
        purpose="investment decision",
        scope="current/near-term",
        constraints="one page",
        time_horizon="12 months",
    )
    assert gm.company == "Example Co"
    assert gm.purpose == "investment decision"
    assert gm.scope == "current/near-term"
    assert gm.constraints == "one page"
    assert gm.time_horizon == "12 months"


def test_2_empty_company_raises_validation_error():
    with pytest.raises(GoalMemoryValidationError):
        GoalMemory(
            company="",
            purpose="investment decision",
            scope="s",
            constraints="c",
            time_horizon="t",
        )


def test_3_none_company_raises_validation_error():
    with pytest.raises(GoalMemoryValidationError):
        GoalMemory(
            company=None,  # type: ignore[arg-type]
            purpose="investment decision",
            scope="s",
            constraints="c",
            time_horizon="t",
        )


def test_4_lock_sets_locked_true():
    gm = GoalMemory(
        company="Example",
        purpose="investment decision",
        scope="s",
        constraints="c",
        time_horizon="t",
    )
    assert not gm.locked
    gm.lock()
    assert gm.locked


def test_5_update_after_lock_raises_locked_error():
    gm = GoalMemory(
        company="Example",
        purpose="investment decision",
        scope="s",
        constraints="c",
        time_horizon="t",
    )
    gm.lock()
    with pytest.raises(GoalMemoryLockedError):
        gm.update("scope", "new scope")


def test_6_to_dict_contains_all_fields():
    gm = GoalMemory(
        company="Example",
        purpose="investment decision",
        scope="current",
        constraints="one page",
        time_horizon="12 months",
    )
    d = gm.to_dict()
    assert d == {
        "company": "Example",
        "purpose": "investment decision",
        "scope": "current",
        "constraints": "one page",
        "time_horizon": "12 months",
    }


def test_7_default_purpose_applied_when_not_provided():
    gm = GoalMemory(
        company="Example",
        purpose=None,  # type: ignore[arg-type]
        scope="s",
        constraints="c",
        time_horizon="t",
    )
    assert gm.purpose == GoalMemory.DEFAULT_PURPOSE
