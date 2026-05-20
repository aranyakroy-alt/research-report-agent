import time
import json

from poc2_research_agent.agents.goal_setter import run_goal_setter
from poc2_research_agent.tracking.cost_tracker import CostTracker
from poc2_research_agent.agents.dimension_generator import run_dimension_generator
import poc2_research_agent.config as config
from poc2_research_agent.memory.episodic_memory import EpisodicMemory
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory
from poc2_research_agent.agents.react_agent import run_react_agent
from poc2_research_agent.report.report_generator import run_report_generator


def run_agent(company_name: str, scenario_id: str = "S-A") -> dict:
    start = time.time()

    # C1
    goal_memory = run_goal_setter(company_name)

    # Cost tracker
    cost_tracker = CostTracker(scenario=scenario_id, company=goal_memory.company)

    # C2
    working_memory = run_dimension_generator(goal_memory, cost_tracker)

    # Memory init
    episodic_memory = EpisodicMemory()
    evaluation_memory = EvaluationMemory()
    for dim in working_memory.dimensions:
        evaluation_memory.add_dimension(dim.id)

    # C3 + C4
    scenario = config.SCENARIOS.get(scenario_id)
    working_memory, episodic_memory, evaluation_memory = run_react_agent(
        goal_memory, working_memory, episodic_memory, evaluation_memory,
        cost_tracker, scenario
    )

    # C5
    brief_path = run_report_generator(
        goal_memory, evaluation_memory, cost_tracker,
        model=None, scenario=scenario_id
    )

    return {
        "brief_path": brief_path,
        "scenario": scenario_id,
        "cost_summary": cost_tracker.get_session_summary(),
        "elapsed_seconds": round(time.time() - start, 2)
    }


if __name__ == "__main__":
    company = "Reliance Industries"
    try:
        result = run_agent(company, "S-A")
        print(json.dumps(result, indent=2))
    except Exception as e:
        # Print exception type and message exactly as they appear
        import traceback
        traceback.print_exc()
        raise
