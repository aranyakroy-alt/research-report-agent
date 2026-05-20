import os
import json
import textwrap

from poc2_research_agent.report.report_generator import run_report_generator, ReportGenerationError
from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory, EvidenceItem


class DummyCT:
	def __init__(self, resp_text="", summary=None, raise_on=False):
		self.resp_text = resp_text or ""
		self.summary = summary or {}
		self.raise_on = raise_on

	def call_llm(self, component=None, model=None, messages=None):
		if self.raise_on:
			raise RuntimeError("llm down")
		return self.resp_text

	def get_session_summary(self):
		return self.summary


def make_goal():
	return GoalMemory(company="Acme Corp", purpose="investment decision", scope="investigate", constraints="", time_horizon="1y")


def make_evm_with_answered():
	evm = EvaluationMemory()
	evm.add_dimension("D1")
	evm.add_evidence("D1", EvidenceItem(fact="f1", stance="SUPPORTS", confidence=0.8, source="s1"))
	evm.add_evidence("D1", EvidenceItem(fact="f2", stance="NEUTRAL", confidence=0.5, source="s2"))
	evm.mark_answered("D1")
	return evm


def test_complete_evaluation_generates_markdown(tmp_path):
	goal = make_goal()
	evm = make_evm_with_answered()
	# simple markdown response containing required sections
	md = textwrap.dedent("""
	# Acme Corp -- Investment Brief
	## Business Overview
	overview
	## Key Financials
	numbers
	## Recent News & Sentiment
	news
	## Key Risks
	risks
	## Sector Outlook
	outlook
	## Investment Thesis
	   Bull Case: good
	   Bear Case: bad
	   Weighted Stance: BUY (Confidence: 70%)
	## Sources
	- s1
	""")

	ct = DummyCT(resp_text=md)
	out = run_report_generator(goal, evm, ct, model="m", scenario="S")
	assert os.path.exists(out)


def test_word_count_within_limit(monkeypatch):
	goal = make_goal()
	evm = make_evm_with_answered()
	# create long but controlled markdown (600 words)
	body = "word " * 600
	md = "# Acme Corp -- Investment Brief\n" + body + "\n## Sources\n- s1\n"
	ct = DummyCT(resp_text=md)
	out = run_report_generator(goal, evm, ct, model="m", scenario="S")
	text = open(out, encoding="utf-8").read()
	assert len(text.split()) <= 650


def test_all_sections_present():
	goal = make_goal()
	evm = make_evm_with_answered()
	md = "# Acme Corp -- Investment Brief\n## Business Overview\n## Key Financials\n## Recent News & Sentiment\n## Key Risks\n## Sector Outlook\n## Investment Thesis\n   Bull Case: x\n   Bear Case: y\n## Sources\n- s1\n"
	ct = DummyCT(resp_text=md)
	out = run_report_generator(goal, evm, ct, model="m", scenario="S")
	text = open(out, encoding="utf-8").read()
	for h in ["## Business Overview", "## Key Financials", "## Recent News & Sentiment", "## Key Risks", "## Sector Outlook", "## Investment Thesis"]:
		assert h in text


def test_bull_and_bear_present():
	goal = make_goal()
	evm = make_evm_with_answered()
	md = "## Investment Thesis\n   Bull Case: up\n   Bear Case: down\n## Sources\n- s1\n"
	ct = DummyCT(resp_text=md)
	out = run_report_generator(goal, evm, ct, model="m", scenario="S")
	text = open(out, encoding="utf-8").read()
	assert "Bull Case" in text and "Bear Case" in text


def test_saved_to_outputs_briefs():
	goal = make_goal()
	evm = make_evm_with_answered()
	md = "# Acme Corp -- Investment Brief\n## Sources\n- s1\n"
	ct = DummyCT(resp_text=md)
	out = run_report_generator(goal, evm, ct, model="m", scenario="S")
	assert "outputs/briefs" in out


def test_empty_evaluation_raises():
	goal = make_goal()
	evm = EvaluationMemory()
	ct = DummyCT(resp_text="irrelevant")
	try:
		run_report_generator(goal, evm, ct, model="m", scenario="S")
		raised = False
	except ReportGenerationError:
		raised = True
	assert raised


def test_sources_section_non_empty():
	goal = make_goal()
	evm = make_evm_with_answered()
	md = "# Acme Corp -- Investment Brief\n## Sources\n- s1\n"
	ct = DummyCT(resp_text=md)
	out = run_report_generator(goal, evm, ct, model="m", scenario="S")
	text = open(out, encoding="utf-8").read()
	assert "## Sources" in text
	sources_part = text.split("## Sources", 1)[1].strip()
	assert len(sources_part) > 0

