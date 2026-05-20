"""Tests for EpisodicMemory and EpisodicEntry."""
import pytest
from datetime import datetime

from poc2_research_agent.memory.episodic_memory import (
    EpisodicEntry,
    EpisodicMemory,
    EpisodicEntryAlreadyExistsError,
    make_key,
)


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def test_1_add_and_retrieve_entry():
    mem = EpisodicMemory()
    e = EpisodicEntry(key="k1", value="v1", source="s", fetched_at=now_iso())
    mem.add(e)
    assert mem.exists("k1")


def test_2_add_duplicate_key_raises():
    mem = EpisodicMemory()
    e = EpisodicEntry(key="k1", value="v1", source="s", fetched_at=now_iso())
    mem.add(e)
    with pytest.raises(EpisodicEntryAlreadyExistsError):
        mem.add(e)


def test_3_get_existing_key_returns_entry():
    mem = EpisodicMemory()
    e = EpisodicEntry(key="k1", value="v1", source="s", fetched_at=now_iso())
    mem.add(e)
    got = mem.get("k1")
    assert got is not None
    assert got.key == "k1"


def test_4_get_missing_key_returns_none():
    mem = EpisodicMemory()
    assert mem.get("missing") is None


def test_5_exists_true_for_stored_key():
    mem = EpisodicMemory()
    e = EpisodicEntry(key="k1", value="v1", source="s", fetched_at=now_iso())
    mem.add(e)
    assert mem.exists("k1")


def test_6_exists_false_for_unknown_key():
    mem = EpisodicMemory()
    assert not mem.exists("unknown")


def test_7_mark_used_appends_dimension_id():
    mem = EpisodicMemory()
    e = EpisodicEntry(key="k1", value="v1", source="s", fetched_at=now_iso())
    mem.add(e)
    mem.mark_used("k1", "D1")
    mem.mark_used("k1", "D2")
    got = mem.get("k1")
    assert got is not None
    assert got.used_by_dimensions == ["D1", "D2"]


def test_8_make_key_normalisation():
    k = make_key("Example Co", "Key Topic")
    assert k == "example_co_key_topic"


def test_9_all_keys_returns_all_stored_keys():
    mem = EpisodicMemory()
    mem.add(EpisodicEntry(key="a", value="v", source="s", fetched_at=now_iso()))
    mem.add(EpisodicEntry(key="b", value="v2", source="s2", fetched_at=now_iso()))
    keys = mem.all_keys()
    assert set(keys) == {"a", "b"}
