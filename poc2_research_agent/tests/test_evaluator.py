import json

from poc2_research_agent.agents.evaluator import run_evaluator
from poc2_research_agent.memory.goal_memory import GoalMemory
from poc2_research_agent.memory.working_memory import WorkingMemory, Dimension
from poc2_research_agent.memory.evaluation_memory import EvaluationMemory, EvidenceItem


class DummyCT:
	def __init__(self, responses=None, raise_on=None):
		# responses: list of strings to return sequentially
		self.responses = responses or []
		self.idx = 0
		self.last_messages = None
		self.raise_on = raise_on

	def call_llm(self, component=None, model=None, messages=None):
		self.last_messages = messages
		if self.raise_on:
			raise RuntimeError("llm down")
		if self.idx < len(self.responses):
			r = self.responses[self.idx]
			self.idx += 1
			return r
		return json.dumps({"stance": "NEUTRAL", "confidence": 0.0, "summary": "n", "gap": None})


def make_goal():
	return GoalMemory(company="Acme Corp", purpose="investment decision", scope="investigate", constraints="", time_horizon="1y")


def test_supports_finding_adds_supports():
	goal = make_goal()
	wm = WorkingMemory()
	dim = Dimension(id="D1", question="Q1")
	wm.add_dimension(dim)
	evm = EvaluationMemory()
	ct = DummyCT(responses=[json.dumps({"stance": "SUPPORTS", "confidence": 0.9, "summary": "ok", "gap": None})])

	run_evaluator(dim, "raw", goal, evm, wm, ct, model="m")
	e = evm.get_evaluation("D1")
	assert any(it.stance == "SUPPORTS" for it in e.evidence)


def test_contradicts_sets_contradiction():
	goal = make_goal()
	wm = WorkingMemory()
	dim = Dimension(id="D1", question="Q1")
	wm.add_dimension(dim)
	evm = EvaluationMemory()
	ct = DummyCT(responses=[json.dumps({"stance": "CONTRADICTS", "confidence": 0.6, "summary": "bad", "gap": None})])

	run_evaluator(dim, "raw", goal, evm, wm, ct, model="m")
	assert evm.has_contradiction("D1")


def test_gap_detected_adds_dimension():
	goal = make_goal()
	wm = WorkingMemory()
	dim = Dimension(id="D1", question="Q1")
	wm.add_dimension(dim)
	evm = EvaluationMemory()
	ct = DummyCT(responses=[json.dumps({"stance": "NEUTRAL", "confidence": 0.5, "summary": "s", "gap": "What about X?"})])

	run_evaluator(dim, "raw", goal, evm, wm, ct, model="m")
	# New dimension added
	assert any(d.question == "What about X?" for d in wm.dimensions)


def test_d6_not_answered_until_first_five_complete():
	goal = make_goal()
	wm = WorkingMemory()
	# create D1..D6
	for i in range(1, 7):
		wm.add_dimension(Dimension(id=f"D{i}", question=f"Q{i}"))

	evm = EvaluationMemory()
	# pre-populate D6 with one SUPPORTS evidence
	evm.add_dimension("D6")
	evm.add_evidence("D6", EvidenceItem(fact="prior", stance="SUPPORTS", confidence=0.8, source="t"))

	ct = DummyCT(responses=[json.dumps({"stance": "SUPPORTS", "confidence": 0.9, "summary": "s", "gap": None})])

	# First run: D1-D5 not answered -> D6 should NOT be marked answered
	run_evaluator(wm.get_dimension("D6"), "raw", goal, evm, wm, ct, model="m")
	assert not evm.get_evaluation("D6").answered


def test_llm_failure_writes_neutral_no_exception():
	goal = make_goal()
	wm = WorkingMemory()
	dim = Dimension(id="D1", question="Q1")
	wm.add_dimension(dim)
	evm = EvaluationMemory()
	ct = DummyCT(raise_on=True)

	# Should not raise
	run_evaluator(dim, "raw", goal, evm, wm, ct, model="m")
	e = evm.get_evaluation("D1")
	assert any(it.stance == "NEUTRAL" and it.confidence == 0.0 for it in e.evidence)


def test_prior_evidence_included_in_prompt():
	goal = make_goal()
	wm = WorkingMemory()
	dim = Dimension(id="D1", question="Q1")
	wm.add_dimension(dim)
	evm = EvaluationMemory()
	evm.add_dimension("D1")
	evm.add_evidence("D1", EvidenceItem(fact="f1", stance="SUPPORTS", confidence=0.9, source="t"))

	ct = DummyCT(responses=[json.dumps({"stance": "NEUTRAL", "confidence": 0.5, "summary": "s", "gap": None})])
	run_evaluator(dim, "raw1", goal, evm, wm, ct, model="m")
	assert ct.last_messages is not None
	joined = "".join(m.get("content", "") for m in ct.last_messages)
	assert "SUPPORTS:f1" in joined


def test_verdict_updated_after_each_new_evidence():
	goal = make_goal()
	wm = WorkingMemory()
	dim = Dimension(id="D1", question="Q1")
	wm.add_dimension(dim)
	evm = EvaluationMemory()
	evm.add_dimension("D1")

	# First response SUPPORTS, second CONTRADICTS to force MIXED
	responses = [json.dumps({"stance": "SUPPORTS", "confidence": 0.8, "summary": "s", "gap": None}), json.dumps({"stance": "CONTRADICTS", "confidence": 0.7, "summary": "s2", "gap": None})]
	ct = DummyCT(responses=responses)

	# Run twice to simulate two new pieces of evidence
	run_evaluator(dim, "raw1", goal, evm, wm, ct, model="m")
	run_evaluator(dim, "raw2", goal, evm, wm, ct, model="m")

	# Verdict should be MIXED
	assert evm.get_evaluation("D1").current_verdict == "MIXED"

