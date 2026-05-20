"""Tests for financial_fetcher, mocking yfinance.Ticker."""
import types
import pytest
from poc2_research_agent.tools.financial_fetcher import financial_fetcher, TICKER_MAP


class DummyTicker:
    def __init__(self, info):
        self.info = info


def test_1_valid_company_and_metrics_returns_metrics(monkeypatch):
    info = {
        "totalRevenue": 1000,
        "netIncome": 100,
        "trailingEps": 2.5,
        "trailingPE": 15.0,
        "marketCap": 1_000_000,
        "currency": "INR",
    }

    yf_mod = types.SimpleNamespace(Ticker=lambda ticker: DummyTicker(info))
    monkeypatch.setitem(__import__("sys").modules, "yfinance", yf_mod)

    comp = list(TICKER_MAP.keys())[0]
    out = financial_fetcher(comp, ["revenue", "net_profit"])
    assert "metrics" in out
    assert out["metrics"]["revenue"]["value"] == 1000
    assert out["metrics"]["net_profit"]["value"] == 100


def test_2_unknown_company_returns_error():
    out = financial_fetcher("Unknown Co", ["revenue"])
    assert "error" in out


def test_3_empty_company_raises_value_error():
    with pytest.raises(ValueError):
        financial_fetcher("", ["revenue"])


def test_4_empty_metrics_list_raises_value_error():
    with pytest.raises(ValueError):
        financial_fetcher("Reliance Industries", [])


def test_5_output_contains_fetched_at(monkeypatch):
    info = {"totalRevenue": 1, "currency": "USD"}
    yf_mod = types.SimpleNamespace(Ticker=lambda ticker: DummyTicker(info))
    monkeypatch.setitem(__import__("sys").modules, "yfinance", yf_mod)
    out = financial_fetcher("Reliance Industries", ["revenue"])
    assert "fetched_at" in out


def test_6_output_contains_company(monkeypatch):
    info = {"totalRevenue": 1, "currency": "USD"}
    yf_mod = types.SimpleNamespace(Ticker=lambda ticker: DummyTicker(info))
    monkeypatch.setitem(__import__("sys").modules, "yfinance", yf_mod)
    out = financial_fetcher("Reliance Industries", ["revenue"])
    assert out.get("company") == "Reliance Industries"


def test_7_yoy_change_pct_is_float(monkeypatch):
    info = {"totalRevenue": 200.0, "totalRevenue_prev": 100.0, "currency": "USD"}
    yf_mod = types.SimpleNamespace(Ticker=lambda ticker: DummyTicker(info))
    monkeypatch.setitem(__import__("sys").modules, "yfinance", yf_mod)
    out = financial_fetcher("Reliance Industries", ["revenue"])
    assert isinstance(out["metrics"]["revenue"]["yoy_change_pct"], float)
