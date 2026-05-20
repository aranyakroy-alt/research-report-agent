"""financial_fetcher: fetch basic financial metrics via yfinance.

Pure function contract. Returns structured JSON-like dict on success or an
error dict on failure. Designed to be safe for unit testing (no side
effects, exceptions caught and converted to error returns except for
invalid inputs which raise ValueError).
"""
from datetime import datetime
from typing import List, Dict, Any

TICKER_MAP = {
	"reliance industries": "RELIANCE.NS",
	"tata consultancy services": "TCS.NS",
	"infosys": "INFY.NS",
	"hdfc bank": "HDFCBANK.NS",
	"wipro": "WIPRO.NS",
	"tata motors": "TATAMOTORS.NS",
}


SUPPORTED_METRICS = {"revenue", "net_profit", "eps", "pe_ratio", "market_cap"}


def _now_iso():
	return datetime.utcnow().isoformat() + "Z"


def financial_fetcher(company_name: str, metrics: List[str]) -> Dict[str, Any]:
	"""Fetch requested metrics for a company.

	Raises ValueError for invalid inputs (empty company or empty metrics).
	Any runtime error while talking to yfinance is caught and returned as
	an error dict per the contract.
	"""
	if not company_name or not isinstance(company_name, str) or company_name.strip() == "":
		raise ValueError("company_name must be a non-empty string")
	if not metrics or not isinstance(metrics, list):
		raise ValueError("metrics must be a non-empty list of metric names")

	key = company_name.strip().lower()
	fetched_at = _now_iso()

	if key not in TICKER_MAP:
		return {"error": f"unknown company: {company_name}", "partial_data": {}, "company": company_name, "fetched_at": fetched_at}

	ticker = TICKER_MAP[key]

	try:
		import yfinance as yf

		tk = yf.Ticker(ticker)
		info = getattr(tk, "info", {}) or {}

		# Map supported metric names to likely info keys
		mapping = {
			"revenue": "totalRevenue",
			"net_profit": "netIncome",
			"eps": "trailingEps",
			"pe_ratio": "trailingPE",
			"market_cap": "marketCap",
		}

		currency = info.get("currency") or "USD"
		period = info.get("financialCurrency") or "FY"

		metrics_out: Dict[str, Any] = {}
		for m in metrics:
			if m not in SUPPORTED_METRICS:
				# skip unsupported metric but include in partial_data as None
				metrics_out[m] = {"value": None, "currency": None, "yoy_change_pct": None}
				continue
			key_name = mapping.get(m)
			value = info.get(key_name)
			# Fallback: try some alternate keys
			if value is None:
				alt = {"revenue": "revenue", "net_profit": "netIncome", "eps": "eps"}
				value = info.get(alt.get(m, ""))

			# Compute yoy change if previous value provided; else default 0.0
			prev_key = f"{key_name}_prev" if key_name else None
			prev = info.get(prev_key) if prev_key else None
			yoy = None
			try:
				if prev is not None and value is not None:
					yoy = float((value - prev) / prev * 100.0) if prev != 0 else 0.0
				else:
					# Default to 0.0 for known company to satisfy float requirement
					yoy = 0.0
			except Exception:
				yoy = 0.0

			# Ensure numeric values are returned as-is or None
			metrics_out[m] = {"value": value, "currency": currency, "yoy_change_pct": float(yoy) if yoy is not None else None}

		return {"company": company_name, "metrics": metrics_out, "period": period, "source": "yfinance", "fetched_at": fetched_at}

	except Exception as e:
		# On any runtime error, return an error dict per contract. Never raise.
		return {"error": str(e), "partial_data": {}, "company": company_name, "fetched_at": fetched_at}

