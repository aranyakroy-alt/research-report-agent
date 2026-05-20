"""Entry point for the POC2 Research & Report Agent.

Usage:
    python -m poc2_research_agent.main [company_name] [scenario_id]
    e.g.: python -m poc2_research_agent.main "Reliance Industries" S-A
"""
import sys
import time

from poc2_research_agent.agents.goal_setter import run_goal_setter
from poc2_research_agent.tracking.cost_tracker import CostTracker
from poc2_research_agent.agents.dimension_generator import run_dimension_generator
from poc2_research_agent.memory.episodic_memory import EpisodicMemory
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory
from poc2_research_agent.agents.react_agent import run_react_agent
from poc2_research_agent.report.report_generator import run_report_generator
import poc2_research_agent.config as config


def run_agent(company_name: str, scenario_id: str = "S-A", on_event=None) -> dict:
    """Full pipeline for one scenario.

    Returns:
        {
            "brief_path": str,
            "scenario": str,
            "cost_summary": dict,
            "elapsed_seconds": float,
        }
    """
    start = time.time()

    scenario = config.SCENARIOS[scenario_id]

    # C1 – goal setter (deterministic)
    goal_memory = run_goal_setter(company_name)
    if on_event:
        on_event("goal_set", {"company": goal_memory.company, "scenario": scenario_id})

    # Cost tracker (anchors log to outputs/cost_log.json)
    cost_tracker = CostTracker(scenario=scenario_id, company=goal_memory.company)

    # C2 – dimension generator
    working_memory = run_dimension_generator(goal_memory, cost_tracker, on_event=on_event)

    # Memory init
    episodic_memory = EpisodicMemory()
    evaluation_memory = EvaluationMemory()
    for dim in working_memory.dimensions:
        evaluation_memory.add_dimension(dim.id)

    # C3 + C4 – ReAct loop + evaluator
    working_memory, episodic_memory, evaluation_memory = run_react_agent(
        goal_memory, working_memory, episodic_memory, evaluation_memory,
        cost_tracker, scenario, on_event=on_event,
    )

    # C5 – report generator
    if on_event:
        on_event("report_generating", {})
    brief_path = run_report_generator(
        goal_memory, evaluation_memory, cost_tracker,
        model=scenario["C5"], scenario=scenario_id, on_event=on_event,
    )

    return {
        "company": company_name,
        "brief_path": brief_path,
        "scenario": scenario_id,
        "cost_summary": cost_tracker.get_session_summary(),
        "elapsed_seconds": round(time.time() - start, 2),
    }


def main():
    company = sys.argv[1] if len(sys.argv) > 1 else "Reliance Industries"
    scenario = sys.argv[2] if len(sys.argv) > 2 else "S-A"
    result = run_agent(company, scenario)
    print(f"Brief: {result['brief_path']}")
    print(f"Cost:  ${result['cost_summary']['total_cost_usd']:.4f}")
    print(f"Time:  {result['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
