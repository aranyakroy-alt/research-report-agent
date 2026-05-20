#!/usr/bin/env python3
"""Run all 6 scenarios sequentially for a company and generate comparison report."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'poc2_research_agent'))

from poc2_research_agent.main import run_agent
from poc2_research_agent.tracking.comparison import generate_comparison_report


def run_all_scenarios(company_name: str) -> str:
    """
    Runs all 6 scenarios sequentially for same company.
    Returns: path to comparison_report.md
    """
    results = []
    scenarios = ["S-A", "S-B", "S-C", "S-D", "S-E", "S-F"]
    for scenario_id in scenarios:
        print(f"Running {scenario_id}...")
        try:
            result = run_agent(company_name, scenario_id)
            results.append(result)
            print(f"  Cost: ${result['cost_summary']['total_cost_usd']:.4f} | Time: {result['elapsed_seconds']}s")
        except Exception as e:
            print(f"  Error: {e}")
            # Skip failed scenarios

    report_path = generate_comparison_report(results, company_name)
    return report_path


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "Reliance Industries"
    report_path = run_all_scenarios(company)
    print(f"Comparison report: {report_path}")