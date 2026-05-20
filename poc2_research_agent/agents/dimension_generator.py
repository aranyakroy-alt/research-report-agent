"""C2: Dimension Generator.

Uses an LLM (via CostTracker) to generate the research dimensions/questions
for the WorkingMemory. This module wraps LLM calls with CostTracker and
validates the returned JSON.
"""
import json
import re
from typing import List

from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.working_memory import WorkingMemory, Dimension
import poc2_research_agent.config as config


SYSTEM = """You are a financial research planning agent.
Given a company name and research goal, generate exactly 6 questions that must 
be answered to produce a complete one-page investment brief.
Rules:
- Question 6 must always be the investment thesis question (bull vs bear case)
- Each question must be specific and answerable with web search or financial data
- Return ONLY a JSON array of 6 strings. No preamble. No markdown.
"""

# Ensure at least one question requests financial metrics explicitly so the
# pipeline triggers the financial_fetcher tool (which looks for keywords like
# 'revenue', 'profit', 'market cap'). Tests and downstream logic depend on the
# generator including such a question.
SYSTEM += "\nAt least one question must explicitly ask about revenue, profit trends, or market cap to ensure financial data is retrieved."

USER = """Company: {company}
Purpose: {purpose}
Scope: {scope}
Generate 6 research questions."""


class DimensionGenerationError(Exception):
	pass


def run_dimension_generator(goal_memory: GoalMemory, cost_tracker, on_event=None) -> WorkingMemory:
	# 1. Validate GoalMemory is locked
	if not getattr(goal_memory, "locked", False):
		raise DimensionGenerationError("GoalMemory must be locked before generating dimensions")

	# 2. Get model for C2 from scenario
	scenario = getattr(cost_tracker, "scenario", None)
	if not scenario or scenario not in config.SCENARIOS:
		raise DimensionGenerationError("Invalid scenario on cost_tracker")
	model = config.SCENARIOS[scenario]["C2"]

	system_msg = SYSTEM
	user_msg = USER.format(company=goal_memory.company, purpose=goal_memory.purpose, scope=goal_memory.scope)

	try:
		resp_text = cost_tracker.call_llm(component="C2", model=model, messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}])
	except Exception as e:
		raise DimensionGenerationError(f"LLM call failed: {e}")

	# 4. Parse JSON response -> list of strings
	try:
		arr = json.loads(resp_text)
		if not isinstance(arr, list):
			raise ValueError("LLM did not return a JSON array")
		questions: List[str] = [str(x).strip() for x in arr]
	except json.JSONDecodeError:
		# Try to extract JSON array with regex
		match = re.search(r'\[.*?\]', resp_text, re.DOTALL)
		if match:
			try:
				arr = json.loads(match.group())
				if isinstance(arr, list):
					questions: List[str] = [str(x).strip() for x in arr]
				else:
					raise ValueError("Extracted content is not a JSON array")
			except json.JSONDecodeError:
				# Retry with stricter prompt
				stricter_user = user_msg + "\n\nIMPORTANT: Return ONLY a valid JSON array. No explanation. No markdown. No code blocks. Start your response with [ and end with ]. Example: [\"question 1\", \"question 2\"]"
				resp_text = cost_tracker.call_llm(component="C2", model=model, messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": stricter_user}])
				arr = json.loads(resp_text)
				if not isinstance(arr, list):
					raise ValueError("Retry did not return a JSON array")
				questions: List[str] = [str(x).strip() for x in arr]
		else:
			# No array found, retry with stricter prompt
			stricter_user = user_msg + "\n\nIMPORTANT: Return ONLY a valid JSON array. No explanation. No markdown. No code blocks. Start your response with [ and end with ]. Example: [\"question 1\", \"question 2\"]"
			resp_text = cost_tracker.call_llm(component="C2", model=model, messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": stricter_user}])
			arr = json.loads(resp_text)
			if not isinstance(arr, list):
				raise ValueError("Retry did not return a JSON array")
			questions: List[str] = [str(x).strip() for x in arr]
	except Exception as e:
		# Catch other exceptions like ValueError
		raise DimensionGenerationError(f"Failed to parse LLM response: {e}")

	# 5. Validate count
	if len(questions) < config.MIN_DIMENSIONS:
		raise DimensionGenerationError(f"Insufficient dimensions generated: {len(questions)}")

	# Take first N (we expect 6)
	questions = questions[: max(6, config.MIN_DIMENSIONS)]

	wm = WorkingMemory()
	ids = set()
	for i, q in enumerate(questions, start=1):
		dim_id = f"D{i}"
		if dim_id in ids:
			raise DimensionGenerationError("Duplicate dimension id")
		ids.add(dim_id)
		wm.add_dimension(Dimension(id=dim_id, question=q))

	# 6. Ensure D6 is the investment thesis question; if not, replace it.
	d6 = wm.get_dimension("D6")
	if not any(k in d6.question.lower() for k in ("invest", "thesis", "bull", "bear")):
		# Replace with a standard investment thesis prompt
		thesis_q = "What is the investment thesis for the company (bull case and bear case)?"
		# update the question in-place
		d6.question = thesis_q

	if on_event:
		on_event("dimensions_ready", {"count": len(wm.dimensions)})

	return wm

