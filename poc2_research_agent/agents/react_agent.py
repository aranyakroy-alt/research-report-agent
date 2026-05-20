"""ReAct agent loop (C3) implementation.

This module provides a simple ReAct-style loop that iterates over
working memory dimensions, queries tools (with episodic caching), and
records evaluations. Designed to be test-friendly: all external calls
are performed via the project's tools and CostTracker so tests can
mock them.
"""
from typing import Tuple, Set
from datetime import datetime

from poc2_research_agent.config import MAX_LOOP_ITERATIONS, MAX_TOOL_CALLS
from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.working_memory import WorkingMemory, Dimension
from poc2_research_agent.memory.episodic_memory import EpisodicMemory, EpisodicEntry, make_key
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory, EvidenceItem

# tools
from poc2_research_agent.tools.financial_fetcher import financial_fetcher
from poc2_research_agent.tools.news_scraper import news_scraper
from poc2_research_agent.tools.web_search_reader import web_search_reader

from poc2_research_agent.tracking.cost_tracker import CostTracker
from poc2_research_agent.agents.evaluator import run_evaluator as evaluator_run


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def select_tool(dimension: Dimension) -> str:
    q = dimension.question.lower()
    if any(w in q for w in ["revenue", "profit", "financial", "kpi", "eps", "market cap"]):
        return "financial_fetcher"
    elif any(w in q for w in ["news", "sentiment", "recent", "event"]):
        return "news_scraper"
    else:
        return "web_search_reader"


METRIC_KEYWORDS = {
    "revenue": "revenue",
    "profit": "net_profit",
    "net income": "net_profit",
    "earnings per share": "eps",
    "eps": "eps",
    "pe ratio": "pe_ratio",
    "price to earnings": "pe_ratio",
    "market cap": "market_cap",
    "market capitalisation": "market_cap",
    "market capitalization": "market_cap",
}

ALL_METRICS = ["revenue", "net_profit", "eps", "pe_ratio", "market_cap"]


def extract_metrics(question: str) -> list:
    """For financial dimensions, always fetch ALL supported metrics.
    
    A single question rarely names every metric explicitly — fetching all at once
    gives the evaluator maximum data to work with.
    """
    return ALL_METRICS


def generate_query(dimension: Dimension, goal_memory: GoalMemory, cost_tracker: CostTracker, model: str) -> str:
    """Use the LLM to rewrite the dimension question into 1-3 short keyword-style
    search queries, like a human analyst would type — not a full sentence question.

    Returns the best single query string (first line).
    """
    prompt = (
        f"You are a financial analyst searching the web for information about {goal_memory.company}.\n"
        f"Rewrite the following research question as 3 SHORT keyword-style search queries "
        f"(like Google searches, not questions). Use phrases an analyst would actually type.\n\n"
        f"Research question: {dimension.question}\n\n"
        f"Rules:\n"
        f"- Each query must be 3-8 words max\n"
        f"- Include the company name in each query\n"
        f"- Include a year (2024 or 2025) where relevant\n"
        f"- No question marks, no 'what is', no 'how does'\n"
        f"- Output exactly 3 lines, one query per line, nothing else"
    )
    out = cost_tracker.call_llm(component="C3", model=model, messages=[{"role": "user", "content": prompt}])
    lines = [l.strip().strip('-').strip() for l in str(out).strip().splitlines() if l.strip()]
    # Return the first non-empty query; caller can use it directly
    return lines[0] if lines else f"{goal_memory.company} {dimension.question[:40]}"


def generate_all_queries(dimension: Dimension, goal_memory: GoalMemory, cost_tracker: CostTracker, model: str) -> list:
    """Generate multiple keyword queries and return all of them for multi-angle search."""
    prompt = (
        f"You are a financial analyst searching the web for information about {goal_memory.company}.\n"
        f"Rewrite the following research question as 3 SHORT keyword-style search queries "
        f"(like Google searches, not questions). Use phrases an analyst would actually type.\n\n"
        f"Research question: {dimension.question}\n\n"
        f"Rules:\n"
        f"- Each query must be 3-8 words max\n"
        f"- Include the company name in each query\n"
        f"- Include a year (2024 or 2025) where relevant\n"
        f"- No question marks, no 'what is', no 'how does'\n"
        f"- Output exactly 3 lines, one query per line, nothing else"
    )
    out = cost_tracker.call_llm(component="C3", model=model, messages=[{"role": "user", "content": prompt}])
    lines = [l.strip().strip('-').strip() for l in str(out).strip().splitlines() if l.strip()]
    if not lines:
        lines = [f"{goal_memory.company} {dimension.question[:40]}"]
    return lines[:3]


def call_tool(tool_name: str, query: str, goal_memory: GoalMemory, dimension: Dimension = None):
    if tool_name == "financial_fetcher":
        # financial_fetcher needs a List[str] of metric names, not a raw query
        metrics = extract_metrics(dimension.question if dimension else query)
        return financial_fetcher(goal_memory.company, metrics)
    elif tool_name == "news_scraper":
        return news_scraper(goal_memory.company, days_back=7)
    elif tool_name == "web_search_reader":
        return web_search_reader(query)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def run_evaluator(dimension, raw_result, goal_memory, evaluation_memory, working_memory, cost_tracker, model):
    # Stub -- real implementation in agents/evaluator.py (SESSION 12)
    # For now: add one NEUTRAL evidence item so loop can progress
    from memory.evaluation_memory import EvidenceItem
    # ensure the dimension exists in evaluation memory
    try:
        evaluation_memory.add_dimension(dimension.id)
    except Exception:
        pass
    item = EvidenceItem(
        fact=str(raw_result)[:200],
        stance="NEUTRAL",
        confidence=0.5,
        source="stub"
    )
    evaluation_memory.add_evidence(dimension.id, item)


def run_react_agent(
    goal_memory: GoalMemory,
    working_memory: WorkingMemory,
    episodic_memory: EpisodicMemory,
    evaluation_memory: EvaluationMemory,
    cost_tracker: CostTracker,
    scenario: dict,
    on_event=None,
) -> Tuple[WorkingMemory, EpisodicMemory, EvaluationMemory]:
    """Main ReAct loop.

    Behavior notes / invariants implemented:
    - Check episodic cache before calling any tool.
    - Never call the same tool with identical query twice within a run.
    - Abide by MAX_TOOL_CALLS and MAX_LOOP_ITERATIONS.
    - Skip D6 until D1-D5 are answered.
    - On tool failure, mark dimension "tool_failure" and continue.
    """
    tool_call_count = 0
    called_tool_queries: Set[tuple] = set()

    def emit(event_type: str, data: dict):
        if on_event:
            on_event(event_type, data)

    for _ in range(MAX_LOOP_ITERATIONS):
        unanswered = working_memory.get_unanswered()
        if not unanswered:
            break

        # Precompute whether D1..D5 are all answered
        def first_five_answered() -> bool:
            ids = {d.id for d in working_memory.dimensions}
            required = [f"D{i}" for i in range(1, 6)]
            return all((id_ not in ids) or (working_memory.get_dimension(id_).status == "answered") for id_ in required)

        for dimension in list(unanswered):
            if tool_call_count >= MAX_TOOL_CALLS:
                break

            # Enforce D6 being last
            if dimension.id == "D6" and not first_five_answered():
                continue

            # Generate queries via LLM helper
            try:
                queries = generate_all_queries(dimension, goal_memory, cost_tracker, scenario.get("C3"))
                query = queries[0]  # primary query for cache key / dedup check
            except Exception:
                working_memory.update_status(dimension.id, "tool_failure")
                continue

            # Cache check
            cache_key = make_key(goal_memory.company, dimension.id)
            if episodic_memory.exists(cache_key):
                raw_result = episodic_memory.get(cache_key).value
                entry = episodic_memory.get(cache_key)
                episodic_memory.mark_used(cache_key, dimension.id)
                tool_name = getattr(entry, "source", "episodic_cache")
                emit("cache_hit", {"dimension": dimension.id, "key": cache_key})
            else:
                tool_name = select_tool(dimension)
                emit("tool_selected", {"dimension": dimension.id, "tool": tool_name})

                # Try each query angle until we get a non-empty result
                raw_result = None
                last_error = None
                queries_to_try = queries if tool_name == "web_search_reader" else [query]
                for q_attempt in queries_to_try:
                    if (tool_name, q_attempt) in called_tool_queries:
                        continue
                    try:
                        result_attempt = call_tool(tool_name, q_attempt, goal_memory, dimension)
                        called_tool_queries.add((tool_name, q_attempt))
                        tool_call_count += 1

                        # If financial_fetcher returned "unknown company", fall through to web search
                        if (
                            tool_name == "financial_fetcher"
                            and isinstance(result_attempt, dict)
                            and "error" in result_attempt
                        ):
                            emit("tool_result", {"dimension": dimension.id, "tool": tool_name, "preview": "unknown company — falling back to web search"})
                            # Re-emit tool_selected for web search
                            tool_name = "web_search_reader"
                            emit("tool_selected", {"dimension": dimension.id, "tool": tool_name})
                            web_results = None
                            for wq in queries:
                                if (tool_name, wq) in called_tool_queries:
                                    continue
                                try:
                                    wr = web_search_reader(wq)
                                    called_tool_queries.add((tool_name, wq))
                                    tool_call_count += 1
                                    if wr and wr != []:
                                        web_results = wr
                                        break
                                    web_results = wr
                                except Exception:
                                    pass
                            raw_result = web_results if web_results is not None else result_attempt
                            break

                        # Accept result if non-empty
                        if result_attempt and result_attempt != [] and str(result_attempt) != '[]':
                            raw_result = result_attempt
                            break
                        else:
                            raw_result = result_attempt  # keep as fallback
                    except Exception as e:
                        last_error = e
                        called_tool_queries.add((tool_name, q_attempt))
                        tool_call_count += 1

                if raw_result is None and last_error is not None:
                    emit("tool_failure", {"dimension": dimension.id, "error": str(last_error)})
                    working_memory.update_status(dimension.id, "tool_failure")
                    continue

                # Append to episodic memory
                episodic_memory.add(EpisodicEntry(
                    key=cache_key,
                    value=str(raw_result),
                    source=tool_name,
                    fetched_at=now_iso(),
                    used_by_dimensions=[dimension.id],
                ))
                emit("tool_result", {"dimension": dimension.id, "tool": tool_name, "preview": str(raw_result)[:100]})
                dim_obj = working_memory.get_dimension(dimension.id)
                dim_obj.tool_used = tool_name

            # Evaluate the raw_result using the centralized evaluator (C4)
            evaluator_run(
                dimension,
                raw_result,
                goal_memory,
                evaluation_memory,
                working_memory,
                cost_tracker,
                scenario.get("C4"),
                tool_source=tool_name,
                on_event=on_event,
            )

            # Update working memory status according to evaluation
            try:
                eval_result = evaluation_memory.get_evaluation(dimension.id)
                if eval_result.answered:
                    working_memory.update_status(dimension.id, "answered")
                    emit("dimension_answered", {"dimension": dimension.id})
                else:
                    working_memory.update_status(dimension.id, "in_progress")
            except Exception:
                # If evaluation missing, mark in_progress
                working_memory.update_status(dimension.id, "in_progress")

    return working_memory, episodic_memory, evaluation_memory
"""C3: ReAct Agent placeholder."""

# No logic yet; placeholder to be implemented later.
