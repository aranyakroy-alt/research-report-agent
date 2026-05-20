"""Tests for EvaluationMemory behaviour and invariants."""
import pytest

from poc2_research_agent.memory.evaluation_memory import (
    EvaluationMemory,
    EvidenceItem,
    DimensionEvaluationNotFoundError,
    InvalidStanceError,
)


def test_1_add_dimension_initialises_empty_evaluation():
    em = EvaluationMemory()
    em.add_dimension("D1")
    ev = em.get_evaluation("D1")
    assert ev.dimension_id == "D1"
    assert ev.evidence == []
    assert ev.current_verdict == "UNDECIDED"


def test_2_add_supports_evidence_sets_verdict_supports():
    em = EvaluationMemory()
    em.add_dimension("D1")
    item = EvidenceItem(fact="f1", stance="SUPPORTS", confidence=0.9, source="s")
    em.add_evidence("D1", item)
    assert em.get_evaluation("D1").current_verdict == "SUPPORTS"


def test_3_add_contradicts_after_supports_sets_mixed():
    em = EvaluationMemory()
    em.add_dimension("D1")
    em.add_evidence("D1", EvidenceItem(fact="f1", stance="SUPPORTS", confidence=0.9, source="s"))
    em.add_evidence("D1", EvidenceItem(fact="f2", stance="CONTRADICTS", confidence=0.8, source="s2"))
    assert em.get_evaluation("D1").current_verdict == "MIXED"


def test_4_has_contradiction_true_when_contradicts_exists():
    em = EvaluationMemory()
    em.add_dimension("D1")
    em.add_evidence("D1", EvidenceItem(fact="f2", stance="CONTRADICTS", confidence=0.7, source="s"))
    assert em.has_contradiction("D1")


def test_5_has_contradiction_false_when_only_supports():
    em = EvaluationMemory()
    em.add_dimension("D1")
    em.add_evidence("D1", EvidenceItem(fact="f1", stance="SUPPORTS", confidence=0.6, source="s"))
    assert not em.has_contradiction("D1")


def test_6_mark_answered_sets_answered_true():
    em = EvaluationMemory()
    em.add_dimension("D1")
    em.mark_answered("D1")
    assert em.get_evaluation("D1").answered


def test_7_all_answered_true_only_when_all_dimensions_answered():
    em = EvaluationMemory()
    em.add_dimension("D1")
    em.add_dimension("D2")
    em.mark_answered("D1")
    assert not em.all_answered()
    em.mark_answered("D2")
    assert em.all_answered()


def test_8_invalid_stance_raises():
    em = EvaluationMemory()
    em.add_dimension("D1")
    with pytest.raises(InvalidStanceError):
        em.add_evidence("D1", EvidenceItem(fact="f", stance="BAD", confidence=0.5, source="s"))


def test_9_confidence_out_of_range_raises_value_error():
    em = EvaluationMemory()
    em.add_dimension("D1")
    with pytest.raises(ValueError):
        em.add_evidence("D1", EvidenceItem(fact="f", stance="SUPPORTS", confidence=1.5, source="s"))


def test_10_get_evaluation_unknown_raises():
    em = EvaluationMemory()
    with pytest.raises(DimensionEvaluationNotFoundError):
        em.get_evaluation("missing")
