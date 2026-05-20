"""Tests for web_search_reader using mocked requests.get."""
import types
import pytest

from poc2_research_agent.tools.web_search_reader import web_search_reader


class DummySearchResp:
    def __init__(self, results, status_code=200):
        self._results = results
        self.status_code = status_code

    def json(self):
        return {"results": self._results}


class DummyPageResp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def test_1_valid_query_returns_list(monkeypatch):
    results = [{"url": "https://a.example", "title": "A", "date": "2020-01-01", "source": "S"}]

    def fake_get(url, params=None, timeout=None):
        if "example.com/search" in url:
            return DummySearchResp(results)
        return DummyPageResp("<html><body><p>Content A</p></body></html>")

    monkeypatch.setattr("poc2_research_agent.tools.web_search_reader.requests.get", fake_get)
    out = web_search_reader("query")
    assert isinstance(out, list)


def test_2_each_item_has_all_keys(monkeypatch):
    results = [{"url": "https://a.example", "title": "A", "date": "2020-01-01", "source": "S"}]

    def fake_get(url, params=None, timeout=None):
        if "example.com/search" in url:
            return DummySearchResp(results)
        return DummyPageResp("<html><body><p>Content A</p></body></html>")

    monkeypatch.setattr("poc2_research_agent.tools.web_search_reader.requests.get", fake_get)
    out = web_search_reader("q")
    item = out[0]
    for k in ("url", "title", "extracted_text", "date", "source"):
        assert k in item


def test_3_empty_query_raises():
    with pytest.raises(ValueError):
        web_search_reader("")


def test_4_max_results_capped(monkeypatch):
    results = []
    for i in range(10):
        results.append({"url": f"https://{i}.example", "title": str(i), "date": "", "source": "S"})

    def fake_get(url, params=None, timeout=None):
        if "example.com/search" in url:
            return DummySearchResp(results)
        return DummyPageResp("<html><body><p>Page</p></body></html>")

    monkeypatch.setattr("poc2_research_agent.tools.web_search_reader.requests.get", fake_get)
    out = web_search_reader("q", max_results=10)
    assert len(out) == 5


def test_5_search_failure_returns_empty(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        raise RuntimeError("network")

    monkeypatch.setattr("poc2_research_agent.tools.web_search_reader.requests.get", fake_get)
    out = web_search_reader("q")
    assert out == []


def test_6_extracted_text_has_no_html(monkeypatch):
    results = [{"url": "https://a.example", "title": "A", "date": "", "source": "S"}]

    def fake_get(url, params=None, timeout=None):
        if "example.com/search" in url:
            return DummySearchResp(results)
        return DummyPageResp("<html><body><h1>Hi</h1><p>More</p></body></html>")

    monkeypatch.setattr("poc2_research_agent.tools.web_search_reader.requests.get", fake_get)
    out = web_search_reader("q")
    assert "<" not in out[0]["extracted_text"] and ">" not in out[0]["extracted_text"]


def test_7_max_results_one(monkeypatch):
    results = [{"url": "https://a.example", "title": "A", "date": "", "source": "S"}, {"url": "https://b.example", "title": "B", "date": "", "source": "S"}]

    def fake_get(url, params=None, timeout=None):
        if "example.com/search" in url:
            return DummySearchResp(results)
        return DummyPageResp("<html><body><p>Page</p></body></html>")

    monkeypatch.setattr("poc2_research_agent.tools.web_search_reader.requests.get", fake_get)
    out = web_search_reader("q", max_results=1)
    assert len(out) <= 1
