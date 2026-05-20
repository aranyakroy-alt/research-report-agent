"""Comparison report generation for scenario analysis.

This module generates a comparison report across multiple scenarios.
"""
import os
from datetime import datetime
from typing import List, Dict, Any
import re


def generate_comparison_report(results: List[Dict[str, Any]], company_name: str) -> str:
    """Generate comparison_report.md from scenario results.

    Args:
        results: List of result dicts from run_agent
        company_name: The company name

    Returns:
        Path to the generated report
    """
    date_str = datetime.now().strftime("%Y%m%d")

    # Calculate metrics for each scenario
    scenario_metrics = []
    for result in results:
        scenario = result["scenario"]
        cost = result["cost_summary"]["total_cost_usd"]
        time_sec = result["elapsed_seconds"]
        brief_path = result["brief_path"]

        # Read brief content
        with open(brief_path, 'r') as f:
            brief_content = f.read()

        # Completeness: count how many of D1-D6 appear in [source: ..., D#] tags / 6
        # If no inline sources, fall back to counting D# mentioned in brief
        source_matches = re.findall(r'\[source: [^,]+, ([^]]+)\]', brief_content)
        unique_dims = set()
        for match in source_matches:
            if re.match(r'D\d+', match):
                unique_dims.add(match)
        if not unique_dims:
            # Fallback: count any D# in the brief
            all_dims = re.findall(r'\b(D\d+)\b', brief_content)
            unique_dims = set(all_dims)
        completeness = len(unique_dims) / 6 * 100

        # Citation coverage: count lines containing "[source:" / total non-empty lines
        lines = brief_content.split('\n')
        num_source_lines = sum(1 for line in lines if '[source:' in line)
        total_non_empty_lines = sum(1 for line in lines if line.strip())
        citation_coverage = num_source_lines / max(total_non_empty_lines, 1) * 100

        scenario_metrics.append({
            "scenario": scenario,
            "cost": cost,
            "time": time_sec,
            "completeness": completeness,
            "citation_coverage": citation_coverage,
            "brief_path": brief_path
        })

    # Calculate best value
    best_value = max(scenario_metrics, key=lambda x: x['completeness'] / x['cost'] if x['cost'] > 0 else 0)

    # Map scenario to result for cost breakdown
    scenario_to_result = {r["scenario"]: r for r in results}

    # Models used mapping
    models_map = {
        "S-A": "All Sonnet",
        "S-B": "All Haiku",
        "S-C": "All GPT-4o",
        "S-D": "All GPT-4o-mini",
        "S-E": "Haiku/Sonnet",
        "S-F": "Mixed"
    }

    # Generate report
    report_lines = [
        "# Research & Report Agent -- Scenario Comparison",
        f"## Company: {company_name}",
        f"## Date: {date_str}",
        "",
        "| Scenario | Models Used | Total Cost | Total Time | Completeness | Citation Coverage |",
        "|----------|-------------|-----------|------------|--------------|-------------------|"
    ]

    for m in scenario_metrics:
        report_lines.append(
            f"| {m['scenario']} | {models_map.get(m['scenario'], 'Unknown')} | ${m['cost']:.4f} | {m['time']}s | {m['completeness']:.1f}% | {m['citation_coverage']:.1f}% |"
        )

    report_lines.extend([
        "",
        "## Winner Per Metric",
        f"- Lowest cost: {min(scenario_metrics, key=lambda x: x['cost'])['scenario']}",
        f"- Fastest: {min(scenario_metrics, key=lambda x: x['time'])['scenario']}",
        f"- Most complete: {max(scenario_metrics, key=lambda x: x['completeness'])['scenario']}",
        f"- Best citation coverage: {max(scenario_metrics, key=lambda x: x['citation_coverage'])['scenario']}",
        "",
        f"## Best Value Scenario",
        f"{best_value['scenario']} (completeness/cost ratio: {best_value['completeness'] / best_value['cost']:.2f})",
        "",
        "## Cost Breakdown by Component",
        "| Scenario | C2 | C3 | C4 | C5 | Total |",
        "|----------|-----|-----|-----|-----|-------|"
    ])

    for m in scenario_metrics:
        res = scenario_to_result[m['scenario']]
        calls = res["cost_summary"]["calls_by_component"]
        c2 = calls.get("C2", {}).get("cost", 0)
        c3 = calls.get("C3", {}).get("cost", 0)
        c4 = calls.get("C4", {}).get("cost", 0)
        c5 = calls.get("C5", {}).get("cost", 0)
        total = c2 + c3 + c4 + c5
        report_lines.append(f"| {m['scenario']} | ${c2:.4f} | ${c3:.4f} | ${c4:.4f} | ${c5:.4f} | ${total:.4f} |")

    report_lines.extend([
        "",
        "## Full Brief Links"
    ])

    for m in scenario_metrics:
        report_lines.append(f"- {m['brief_path']}")

    report_content = "\n".join(report_lines)

    # Write to file
    output_dir = "poc2_research_agent/outputs"
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "comparison_report.md")
    with open(report_path, 'w') as f:
        f.write(report_content)

    return report_path
