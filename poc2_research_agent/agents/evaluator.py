"""Evaluator (C4) implementation.

Calls an LLM (via CostTracker) to judge a single finding for a given
dimension and updates EvaluationMemory and WorkingMemory accordingly.
"""
from typing import Optional
import json

from poc2_research_agent.memory.working_memory import WorkingMemory, Dimension
from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory, EvidenceItem
from poc2_research_agent.tracking.cost_tracker import CostTracker


SYSTEM = """You are a decisive financial research evaluator.
Assess whether a finding clearly SUPPORTS or CONTRADICTS the research question.
Only return valid JSON (no markdown, no explanation) in this exact format:
{
    "stance": "SUPPORTS" or "CONTRADICTS" or "NEUTRAL",
    "confidence": float between 0.0 and 1.0,
    "summary": "one-sentence summary of how the finding affects the question",
    "gap": "one concise follow-up research question this finding raises, or null"
}

Guidance for classification:
- Be decisive: prefer SUPPORTS or CONTRADICTS when the finding contains specific, relevant facts or numbers (e.g., revenue, profit trends, market cap, material events).
- Use NEUTRAL only when the finding is clearly unrelated, ambiguous, or lacks information to judge the claim.
- Choose a confidence that reflects strength and directness of the evidence (>=0.7 = strong, 0.4-0.7 = moderate, <0.4 = weak). Avoid defaulting to 0.5.
"""


USER_TMPL = """Company: {company}
Research goal: {purpose}
Dimension: {question}
Finding: {raw_result}
Prior evidence on this dimension: {prior_evidence}

Assess this finding."""


def _next_dimension_id(working_memory: WorkingMemory) -> str:
    # Find max numeric D index and add 1
    max_n = 0
    for d in working_memory.dimensions:
        if d.id.startswith("D"):
            try:
                n = int(d.id[1:])
                if n > max_n:
                    max_n = n
            except Exception:
                continue
    return f"D{max_n + 1}"


def run_evaluator(
    dimension: Dimension,
    raw_result: str,
    goal_memory: GoalMemory,
    evaluation_memory: EvaluationMemory,
    working_memory: WorkingMemory,
    cost_tracker: CostTracker,
    model: str,
    tool_source: str = "llm_evaluator",
    on_event=None,
) -> None:
    """Evaluate a finding and update memories in-place.

    Invariant: read prior evidence before writing. On any LLM or parse
    failure, write a NEUTRAL evidence item with confidence 0.0 and do not
    raise.
    """
    # 1. Read prior evidence
    prior = []
    try:
        ev = evaluation_memory.get_evaluation(dimension.id)
        prior = [f"{it.stance}:{it.fact}" for it in ev.evidence]
    except Exception:
        prior = []

    prior_evidence = "; ".join(prior) if prior else "none"

    # Prepare prompt
    user = USER_TMPL.format(
        company=goal_memory.company,
        purpose=goal_memory.purpose,
        question=dimension.question,
        raw_result=str(raw_result),
        prior_evidence=prior_evidence,
    )

    # Call LLM via cost_tracker
    try:
        resp = cost_tracker.call_llm(component="C4", model=model, messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}])
        text = str(resp)
        parsed = json.loads(text)
    except Exception:
        # LLM/parsing failure -> write NEUTRAL evidence
        try:
            evaluation_memory.add_dimension(dimension.id)
        except Exception:
            pass
        evaluation_memory.add_evidence(
            dimension.id,
            EvidenceItem(fact=str(raw_result)[:200], stance="NEUTRAL", confidence=0.0, source="evaluator_error"),
        )
        return

    # Validate parsed JSON
    stance = parsed.get("stance")
    confidence = parsed.get("confidence")
    summary = parsed.get("summary")
    gap = parsed.get("gap")

    if stance not in {"SUPPORTS", "CONTRADICTS", "NEUTRAL"}:
        # treat as neutral
        stance = "NEUTRAL"
        confidence = 0.0

    try:
        confidence = float(confidence)
        if confidence < 0.0 or confidence > 1.0:
            confidence = 0.0
    except Exception:
        confidence = 0.0

    # Ensure dimension exists
    try:
        evaluation_memory.add_dimension(dimension.id)
    except Exception:
        pass

    # Add evidence
    item = EvidenceItem(fact=(summary or str(raw_result))[:200], stance=stance, confidence=confidence, source=tool_source)
    evaluation_memory.add_evidence(dimension.id, item)

    # Emit evaluation event
    if on_event:
        on_event("evaluation", {"dimension": dimension.id, "stance": stance, "source": tool_source, "confidence": confidence})

    # Recalculate verdict already done by add_evidence

    # Check answered: at least one non-NEUTRAL evidence with confidence >= 0.5
    ev = evaluation_memory.get_evaluation(dimension.id)
    non_neutral_confident = any(
        it.stance in {"SUPPORTS", "CONTRADICTS"} and it.confidence >= 0.5
        for it in ev.evidence
    )
    if non_neutral_confident:
        # Never mark D6 answered until D1-D5 are all answered
        if dimension.id == "D6":
            first_five = [f"D{i}" for i in range(1, 6)]
            all_first_five_answered = all((any(d.id == fid and d.status == "answered" for d in working_memory.dimensions)) for fid in first_five)
            if not all_first_five_answered:
                return
        evaluation_memory.mark_answered(dimension.id)

    # If gap provided, add a new dimension to working memory
    if gap and isinstance(gap, str) and gap.strip():
        new_q = gap.strip()
        new_id = _next_dimension_id(working_memory)
        try:
            working_memory.add_dimension(Dimension(id=new_id, question=new_q))
            if on_event:
                on_event("gap_found", {"question": new_q})
        except Exception:
            # ignore dup id or other errors
            pass
"""C4: Evaluator placeholder."""

# No logic yet; placeholder to be implemented later.
