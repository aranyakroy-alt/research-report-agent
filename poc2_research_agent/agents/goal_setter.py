"""C1: Goal Setter - deterministic GoalMemory creator.

Provides `run_goal_setter(user_input)` which validates and normalises the
company name, fills default fields and returns a locked GoalMemory.
No LLM calls.
"""
from typing import Optional

from poc2_research_agent.memory.goal_memory import GoalMemory, GoalMemoryValidationError


DEFAULT_PURPOSE = "investment decision"
DEFAULT_SCOPE = "current situation and near-term outlook"
DEFAULT_CONSTRAINTS = "one page, cited sources, balanced thesis"
DEFAULT_TIME_HORIZON = "current / next 12 months"


def _normalise_company(name: str) -> str:
	# Basic normalisation: strip and title-case each word
	return " ".join(part.capitalize() for part in name.strip().split())


def run_goal_setter(user_input: Optional[str]) -> GoalMemory:
	"""Create, validate, lock and return a GoalMemory from raw user input.

	Raises GoalMemoryValidationError when input invalid.
	"""
	if user_input is None or not isinstance(user_input, str) or user_input.strip() == "":
		raise GoalMemoryValidationError("company name must be a non-empty string")
	if len(user_input.strip()) < 2:
		raise GoalMemoryValidationError("company name must be at least 2 characters")

	company = _normalise_company(user_input)

	gm = GoalMemory(
		company=company,
		purpose=DEFAULT_PURPOSE,
		scope=DEFAULT_SCOPE,
		constraints=DEFAULT_CONSTRAINTS,
		time_horizon=DEFAULT_TIME_HORIZON,
	)
	# validate is called in GoalMemory.__post_init__, but ensure it's valid
	gm.validate()
	gm.lock()
	return gm

