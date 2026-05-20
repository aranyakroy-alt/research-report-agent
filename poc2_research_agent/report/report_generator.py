"""Report generator (C5) for one-page investment briefs.
"""
import os
from datetime import datetime
from typing import Dict

from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory
from poc2_research_agent.tracking.cost_tracker import CostTracker


class ReportGenerationError(Exception):
    pass


SYSTEM = """You are a financial research writer producing a one-page investment brief.
Write clearly for a non-expert investor.
Every claim must reference a source from the evidence provided.
Be balanced -- include both bull and bear case in the investment thesis.
Maximum 650 words total.
"""


USER_TMPL = """Company: {company}
Research findings:
{formatted_evaluation_memory}

Write the investment brief in this exact structure:
# [Company] -- Investment Brief
## Business Overview
## Key Financials
## Recent News & Sentiment
## Key Risks
## Sector Outlook
## Investment Thesis
   Bull Case: ...
   Bear Case: ...
   Weighted Stance: BUY / HOLD / AVOID (Confidence: X%)
## Sources
"""


def _format_evaluation_memory(evaluation_memory: EvaluationMemory) -> str:
    parts = []
    for dim_id, ev in evaluation_memory.to_dict().get("evaluations", {}).items():
        parts.append(f"- {dim_id}: verdict={ev['current_verdict']}; answered={ev['answered']}")
        for it in ev["evidence"]:
            parts.append(f"    - {it['stance']} ({it['confidence']}): {it['fact']} [source={it['source']}]")
    return "\n".join(parts)


def run_report_generator(
    goal_memory: GoalMemory,
    evaluation_memory: EvaluationMemory,
    cost_tracker: CostTracker,
    model: str,
    scenario: str,
    on_event=None,
) -> str:
    # 1. Validate at least one answered dimension (warn-only; still generate on partial data)
    any_answered = any(ev.answered for ev in evaluation_memory.evaluations.values())
    any_evidence = any(len(ev.evidence) > 0 for ev in evaluation_memory.evaluations.values())
    if not any_answered and not any_evidence:
        raise ReportGenerationError("No answered dimensions or evidence available to generate report")

    # 2. Format evaluation memory
    formatted = _format_evaluation_memory(evaluation_memory)

    # 3. Call LLM via cost_tracker
    user = USER_TMPL.format(company=goal_memory.company, formatted_evaluation_memory=formatted)
    try:
        resp = cost_tracker.call_llm(component="C5", model=model, messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
        brief_md = str(resp)
    except Exception as e:
        raise ReportGenerationError(f"LLM error: {e}")

    # 4. Get session summary (not used further here but per spec we retrieve it)
    try:
        _summary = cost_tracker.get_session_summary()
    except Exception:
        _summary = {}

    # 5. Save brief
    out_dir = os.path.join("poc2_research_agent", "outputs", "briefs")
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.utcnow().strftime("%Y%m%d")
    safe_company = goal_memory.company.lower().replace(" ", "_")
    filename = f"{safe_company}_{scenario}_{date_str}.md"
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(brief_md)

    # 6. Return file path
    if on_event:
        on_event("report_ready", {"path": path})
    return path
"""C5: Report Generator placeholder."""

# No logic yet; placeholder to be implemented later.
