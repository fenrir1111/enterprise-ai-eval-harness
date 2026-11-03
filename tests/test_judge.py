from ai_eval_harness.dataset.models import EvalCase
from ai_eval_harness.judge.deterministic import DeterministicJudge
from ai_eval_harness.judge.llm import LLMJudge


def test_deterministic_judge_correct():
    case = EvalCase(id="x", question="q", golden_answer="须部门负责人审批且限本人阅读")
    score, reason = DeterministicJudge().score(case, "须部门负责人审批且限本人阅读", "ok")
    assert score == 1.0


def test_deterministic_judge_wrong_low():
    case = EvalCase(id="x", question="q", golden_answer="须部门负责人审批且限本人阅读")
    score, _ = DeterministicJudge().score(case, "需审批", "ok")
    assert score < 1.0


def test_llm_judge_unavailable_falls_back():
    case = EvalCase(id="x", question="q", golden_answer="须部门负责人审批且限本人阅读")
    judge = LLMJudge(model="gpt-4o-mini", api_key="")  # 未配置 key
    assert judge.available is False
    score, reason = judge.score(case, "须部门负责人审批且限本人阅读", "ok")
    assert score == 1.0  # 回退确定性判分
    assert reason  # 有回退原因
