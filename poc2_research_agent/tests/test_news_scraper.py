"""Tests for news_scraper tool with NewsAPI mocked via requests."""
import types
import pytest
from datetime import datetime

from poc2_research_agent.tools.news_scraper import news_scraper
import poc2_research_agent.config as config


def make_article(title, desc, source_name, published_at=None):
    return {
        "title": title,
        "description": desc,
        "source": {"name": source_name},
        "publishedAt": published_at or datetime.utcnow().isoformat() + "Z",
        "url": "https://example.com/article",
    }


def test_1_valid_company_returns_list(monkeypatch):
    # Ensure NEWS_API_KEY non-empty so code calls API path
    monkeypatch.setattr(config, "NEWS_API_KEY", "fake-key")

    articles = [make_article("Title 1", "Summary 1", "SourceA")]

    class DummyResp:
        status_code = 200

        def json(self):
            return {"articles": articles}

    def fake_get(url, params, timeout):
        return DummyResp()

    monkeypatch.setattr("poc2_research_agent.tools.news_scraper.requests.get", fake_get)
    out = news_scraper("Reliance Industries")
    assert isinstance(out, list)


def test_2_each_item_has_required_keys(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "fake-key")
    articles = [make_article("Title", "Desc", "S")]

    class DummyResp:
        status_code = 200

        def json(self):
            return {"articles": articles}

    monkeypatch.setattr("poc2_research_agent.tools.news_scraper.requests.get", lambda *a, **k: DummyResp())
    out = news_scraper("Reliance Industries")
    assert len(out) == 1
    item = out[0]
    for k in ("headline", "source", "date", "summary", "url", "sentiment_signal"):
        assert k in item


def test_3_sentiment_is_valid(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "fake-key")
    articles = [make_article("Neutral title", "No keywords here", "S")]

    class DummyResp:
        status_code = 200

        def json(self):
            return {"articles": articles}

    monkeypatch.setattr("poc2_research_agent.tools.news_scraper.requests.get", lambda *a, **k: DummyResp())
    out = news_scraper("Reliance Industries")
    assert out[0]["sentiment_signal"] in {"POSITIVE", "NEGATIVE", "NEUTRAL"}


def test_4_negative_keyword_in_headline_results_negative(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "fake-key")
    articles = [make_article("Company faces lawsuit", "Details", "S")]

    class DummyResp:
        status_code = 200

        def json(self):
            return {"articles": articles}

    monkeypatch.setattr("poc2_research_agent.tools.news_scraper.requests.get", lambda *a, **k: DummyResp())
    out = news_scraper("Reliance Industries")
    assert out[0]["sentiment_signal"] == "NEGATIVE"


def test_5_empty_company_name_raises():
    with pytest.raises(ValueError):
        news_scraper("")


def test_6_api_failure_returns_empty_list(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "fake-key")

    def fake_get(url, params, timeout):
        raise RuntimeError("network fail")

    monkeypatch.setattr("poc2_research_agent.tools.news_scraper.requests.get", fake_get)
    out = news_scraper("Reliance Industries")
    assert out == []


def test_7_returns_maximum_10_articles(monkeypatch):
    monkeypatch.setattr(config, "NEWS_API_KEY", "fake-key")
    articles = [make_article(f"Title {i}", "Desc", "S") for i in range(20)]

    class DummyResp:
        status_code = 200

        def json(self):
            return {"articles": articles}

    monkeypatch.setattr("poc2_research_agent.tools.news_scraper.requests.get", lambda *a, **k: DummyResp())
    out = news_scraper("Reliance Industries")
    assert len(out) == 10


def test_8_days_back_zero_raises():
    with pytest.raises(ValueError):
        news_scraper("Reliance Industries", days_back=0)
