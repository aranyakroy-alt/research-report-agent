# Research & Report Agent — POC 2

[![GitHub](https://img.shields.io/badge/GitHub-aranyakroy--alt%2Fresearch--report--agent-181717?logo=github)](https://github.com/aranyakroy-alt/research-report-agent)

A multi-agent investment research system that autonomously researches a company across six analyst dimensions, gathers evidence from financial data and web sources, and produces a structured investment brief with a verdict and confidence score.

---

## Architecture

```
C1 Goal Setter         →  Parses company + scenario into a structured goal
C2 Dimension Generator →  Generates 6 research dimensions via LLM
C3 ReAct Loop          →  Iterates: select tool → query → cache check → call
C4 Evaluator           →  Scores each result (SUPPORTS / NEUTRAL / CONTRADICTS)
C5 Report Generator    →  Synthesises evidence into a markdown investment brief
```

**Tools available to C3:**
- `financial_fetcher` — yfinance (revenue, net profit, EPS, P/E, market cap)
- `news_scraper` — recent headlines via RSS/scraping
- `web_search_reader` — DuckDuckGo search + page extraction

**Memory:**
- `GoalMemory` — company + scenario intent
- `WorkingMemory` — dimensions + status (pending / in_progress / answered / tool_failure)
- `EpisodicMemory` — tool result cache keyed by company × dimension
- `EvaluationMemory` — evidence items + stance aggregation per dimension

---

## Scenarios

| ID  | C2 Model       | C3 Model       | C4 Model       | C5 Model       |
|-----|----------------|----------------|----------------|----------------|
| S-A | GPT-4o         | GPT-4o         | GPT-4o         | Claude Sonnet  |
| S-B | Claude Haiku   | Claude Haiku   | Claude Haiku   | Claude Haiku   |
| S-C | GPT-4o-mini    | GPT-4o-mini    | GPT-4o-mini    | GPT-4o-mini    |
| S-D | Claude Haiku   | GPT-4o-mini    | Claude Haiku   | Claude Haiku   |
| S-E | Claude Haiku   | Claude Haiku   | Claude Haiku   | Claude Sonnet  |
| S-F | GPT-4o         | GPT-4o-mini    | GPT-4o         | Claude Sonnet  |

---

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API key
- OpenAI API key

### Install

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r poc2_research_agent/requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### Configure

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and OPENAI_API_KEY
```

### Run

```bash
chmod +x run.sh
./run.sh
```

Opens:
- **Frontend** → `http://localhost:3000`
- **Backend API** → `http://localhost:8000/docs`

---

## Frontend

Two-panel desktop webapp with live SSE agent trace streaming.

| Panel | Contents |
|---|---|
| Left (Agent Trace) | Live phase-by-phase trace: Goal Setter → Dimension Generator → ReAct Loop → Report Generator. Colour-coded events: tool calls, cache hits, evaluations, gap dimensions. |
| Right (Results) | Metrics (cost, time, dimensions answered), dynamic dimension grid (D1–D6 + gap dims), verdict bar (stance + confidence), collapsible investment brief sections. |

**Top bar:** company input, scenario selector, Run ↗ button, History drawer.

---

## CLI Usage

```bash
# Single run
python -m poc2_research_agent.main "Reliance Industries" S-A

# All 6 scenarios
python run_all_scenarios.py "Infosys"
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/run` | Start a run → `{job_id}` |
| GET | `/api/stream/{job_id}` | SSE stream of agent events |
| GET | `/api/history` | Last 20 runs |
| GET | `/api/history/{company}` | Runs for a specific company |
| GET | `/api/brief?path=...` | Raw markdown brief (plain text) |

---

## SSE Event Types

| Event | Data |
|---|---|
| `goal_set` | `company`, `scenario` |
| `dimensions_ready` | `count` |
| `tool_selected` | `dimension`, `tool` |
| `cache_hit` | `dimension`, `key` |
| `tool_result` | `dimension`, `tool`, `preview` |
| `tool_failure` | `dimension`, `error` |
| `evaluation` | `dimension`, `stance`, `confidence`, `source` |
| `gap_found` | `question` |
| `dimension_answered` | `dimension` |
| `report_generating` | _(empty)_ |
| `report_ready` | `path` |
| `complete` | full result dict |
| `error` | `message` |

---

## Tests

```bash
source .venv/bin/activate
pytest poc2_research_agent/tests/ -q
```

107 unit tests across all agents, tools, memory modules, and cost tracker.

---

## Project Structure

```
poc2_research_agent/
├── agents/
│   ├── goal_setter.py
│   ├── dimension_generator.py
│   ├── react_agent.py
│   └── evaluator.py
├── tools/
│   ├── financial_fetcher.py
│   ├── news_scraper.py
│   └── web_search_reader.py
├── memory/
│   ├── goal_memory.py
│   ├── working_memory.py
│   ├── episodic_memory.py
│   └── evaluation_memory.py
├── report/
│   └── report_generator.py
├── tracking/
│   ├── cost_tracker.py
│   └── comparison.py
├── api/
│   ├── main.py        ← FastAPI app
│   └── history.py     ← SQLite persistence
├── tests/
└── config.py
frontend/
├── src/
│   ├── components/    ← AgentTrace, ResultsPanel, DimensionGrid, ...
│   ├── hooks/         ← useAgentStream, useHistory
│   └── types.ts
run.sh                 ← starts both backend + frontend
run_all_scenarios.py   ← runs all 6 scenarios for a company
```
