"""Tests for WorkingMemory and Dimension dataclasses."""
import pytest

from poc2_research_agent.memory.working_memory import (
    Dimension,
    WorkingMemory,
    DimensionAlreadyExistsError,
    DimensionNotFoundError,
)


def test_1_add_and_get_dimension():
    wm = WorkingMemory()
    d = Dimension(id="D1", question="Q1")
    wm.add_dimension(d)
    got = wm.get_dimension("D1")
    assert got is d


def test_2_add_duplicate_id_raises():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1"))
    with pytest.raises(DimensionAlreadyExistsError):
        wm.add_dimension(Dimension(id="D1", question="Q1-dup"))


def test_3_get_unanswered_only_returns_unanswered():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1", status="unanswered"))
    wm.add_dimension(Dimension(id="D2", question="Q2", status="answered"))
    wm.add_dimension(Dimension(id="D3", question="Q3", status="in_progress"))
    unanswered = wm.get_unanswered()
    assert len(unanswered) == 1
    assert unanswered[0].id == "D1"


def test_4_update_status_valid_updates():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1"))
    wm.update_status("D1", "in_progress")
    assert wm.get_dimension("D1").status == "in_progress"


def test_5_update_status_invalid_raises_value_error():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1"))
    with pytest.raises(ValueError):
        wm.update_status("D1", "bad_status")


def test_6_all_answered_false_when_unanswered_exists():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1", status="answered"))
    wm.add_dimension(Dimension(id="D2", question="Q2", status="unanswered"))
    assert not wm.all_answered()


def test_7_all_answered_true_when_all_answered():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1", status="answered"))
    wm.add_dimension(Dimension(id="D2", question="Q2", status="tool_failure"))
    assert wm.all_answered()


def test_8_add_evidence_appends_to_dimension():
    wm = WorkingMemory()
    wm.add_dimension(Dimension(id="D1", question="Q1"))
    wm.add_evidence("D1", "fact-1")
    wm.add_evidence("D1", "fact-2")
    assert wm.get_dimension("D1").evidence == ["fact-1", "fact-2"]


def test_9_get_dimension_unknown_raises():
    wm = WorkingMemory()
    with pytest.raises(DimensionNotFoundError):
        wm.get_dimension("missing")
