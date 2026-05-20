"""news_scraper: fetch recent news for a company and classify sentiment.

Pure function contract. Uses NewsAPI when `NEWS_API_KEY` is set in
`poc2_research_agent.config`. If the API key is empty, returns mocked
neutral articles for testing. Never raises unhandled exceptions; returns
an empty list on runtime failures.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any

import poc2_research_agent.config as config
import requests


POSITIVE_KEYWORDS = ["growth", "profit", "expansion", "record", "launch", "partnership", "acquisition", "upgrade", "beat", "surpass"]
NEGATIVE_KEYWORDS = ["loss", "decline", "fine", "penalty", "lawsuit", "cut", "drop", "downgrade", "debt", "miss", "fraud", "probe"]

MAX_ARTICLES = 10


def _classify_sentiment(text: str) -> str:
	t = (text or "").lower()
	for kw in NEGATIVE_KEYWORDS:
		if kw in t:
			return "NEGATIVE"
	for kw in POSITIVE_KEYWORDS:
		if kw in t:
			return "POSITIVE"
	return "NEUTRAL"


def _make_item(article: Dict[str, Any]) -> Dict[str, Any]:
	title = article.get("title") or ""
	source = article.get("source", {}).get("name") if isinstance(article.get("source"), dict) else article.get("source")
	published = article.get("publishedAt") or article.get("published_at") or datetime.utcnow().isoformat() + "Z"
	summary = article.get("description") or article.get("summary") or ""
	url = article.get("url") or ""
	sentiment = _classify_sentiment(title + " " + summary)
	return {
		"headline": title,
		"source": source or "",
		"date": published,
		"summary": summary,
		"url": url,
		"sentiment_signal": sentiment,
	}


def news_scraper(company_name: str, days_back: int = 30) -> List[Dict[str, Any]]:
	if not company_name or not isinstance(company_name, str) or company_name.strip() == "":
		raise ValueError("company_name must be a non-empty string")
	if not isinstance(days_back, int) or days_back < 1:
		raise ValueError("days_back must be an integer >= 1")

	# If API key not configured, return mock data for testing
	if not getattr(config, "NEWS_API_KEY", ""):
		items = []
		for i in range(3):
			items.append({
				"headline": f"{company_name} neutral update {i+1}",
				"source": "mock",
				"date": datetime.utcnow().isoformat() + "Z",
				"summary": "No significant news.",
				"url": "",
				"sentiment_signal": "NEUTRAL",
			})
		return items

	try:
		to_date = datetime.utcnow()
		from_date = to_date - timedelta(days=days_back)
		url = "https://newsapi.org/v2/everything"
		params = {
			"q": company_name,
			"from": from_date.date().isoformat(),
			"to": to_date.date().isoformat(),
			"language": "en",
			"sortBy": "relevancy",
			"pageSize": 100,
			"apiKey": config.NEWS_API_KEY,
		}
		resp = requests.get(url, params=params, timeout=10)
		if resp.status_code != 200:
			return []
		data = resp.json()
		articles = data.get("articles", []) or []
		items: List[Dict[str, Any]] = []
		for a in articles[:MAX_ARTICLES]:
			item = _make_item(a)
			# ensure sentiment_signal validity
			if item["sentiment_signal"] not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
				item["sentiment_signal"] = "NEUTRAL"
			items.append(item)
		return items[:MAX_ARTICLES]
	except Exception:
		# Per contract, never raise; return empty list on failure
		return []

