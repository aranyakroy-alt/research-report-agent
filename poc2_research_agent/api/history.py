"""SQLite history store for agent runs."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "outputs" / "history.db")


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            scenario TEXT,
            cost_usd REAL,
            elapsed_seconds REAL,
            completeness REAL,
            citation_coverage REAL,
            stance TEXT,
            confidence REAL,
            brief_path TEXT,
            brief_text TEXT,
            run_date TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_run(result: dict, brief_text: str = ""):
    """Called after a successful run_agent() completion."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO runs
        (company, scenario, cost_usd, elapsed_seconds,
         completeness, citation_coverage, stance, confidence,
         brief_path, brief_text, run_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            result.get("company", ""),
            result.get("scenario", ""),
            result.get("cost_summary", {}).get("total_cost_usd", 0),
            result.get("elapsed_seconds", 0),
            result.get("completeness", 0),
            result.get("citation_coverage", 0),
            result.get("stance", "UNKNOWN"),
            result.get("confidence", 0),
            result.get("brief_path", ""),
            brief_text,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_history(company: str = None, limit: int = 20) -> list:
    conn = sqlite3.connect(DB_PATH)
    if company:
        rows = conn.execute(
            """
            SELECT company, scenario, cost_usd, elapsed_seconds,
                   completeness, stance, confidence, run_date, brief_path
            FROM runs WHERE company = ?
            ORDER BY run_date DESC LIMIT ?
            """,
            (company, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT company, scenario, cost_usd, elapsed_seconds,
                   completeness, stance, confidence, run_date, brief_path
            FROM runs ORDER BY run_date DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    conn.close()
    cols = ["company", "scenario", "cost_usd", "elapsed_seconds",
            "completeness", "stance", "confidence", "run_date", "brief_path"]
    return [dict(zip(cols, row)) for row in rows]


def get_brief_text(brief_path: str) -> str:
    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
