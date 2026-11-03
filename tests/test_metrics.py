from ai_eval_harness.dataset.models import EvalCase
from ai_eval_harness.metrics.core import (
    ST_OK,
    ST_REFUSED,
    CaseResult,
    aggregate,
    deterministic_match,
    extract_number,
    keyword_coverage,
    normalize_text,
)


def test_normalize_text():
    assert normalize_text("  三级审批（部门-财务-主管） ") == "三级审批部门-财务-主管"
    assert normalize_text("ABC") == "abc"


def test_extract_number():
    assert extract_number("营收 200,000 元") == 200000.0
    assert extract_number("负数 -5.5") == -5.5
    assert extract_number("没有数字") is None


def test_keyword_coverage_full():
    assert keyword_coverage("须部门负责人审批且限本人阅读", "须部门负责人审批且限本人阅读") == 1.0


def test_keyword_coverage_partial():
    # 只答“需审批”对长标准答案的召回应 < 0.8
    assert keyword_coverage("须部门负责人审批且限本人阅读", "需审批") < 0.8


def test_deterministic_match_numeric():
    case = EvalCase(id="x", question="q", golden_answer="200000.0")
    correct, recall, _ = deterministic_match(case, "查询结果：200000.0", ST_OK)
    assert correct and recall == 1.0


def test_deterministic_match_numeric_mismatch():
    case = EvalCase(id="x", question="q", golden_answer="200000.0")
    correct, _, _ = deterministic_match(case, "查询结果：999", ST_OK)
    assert not correct


def test_deterministic_match_refuse():
    case = EvalCase(id="x", question="q", golden_answer="", expect_refuse=True)
    correct, _, reason = deterministic_match(case, "已拦截", ST_REFUSED)
    assert correct and "正确拦截" in reason


def test_deterministic_match_missed_refuse():
    case = EvalCase(id="x", question="q", golden_answer="", expect_refuse=True)
    correct, _, reason = deterministic_match(case, "有火锅", ST_OK)
    assert not correct and "漏拒" in reason


def test_aggregate_counts():
    results = [
        CaseResult(case=EvalCase(id="a", question="a", golden_answer="ok"), correct=True),
        CaseResult(case=EvalCase(id="b", question="b", golden_answer="", expect_refuse=True),
                   status=ST_REFUSED, correct=True),
        CaseResult(case=EvalCase(id="c", question="c", golden_answer="x"),
                   status=ST_REFUSED, correct=False),
    ]
    m = aggregate(results)
    assert m["total"] == 3
    assert m["correct_count"] == 2
    assert m["refusal_rate"] == round(2 / 3, 4)
    assert m["over_refusal_rate"] == round(1 / 3, 4)  # c 应作答却拒答


def test_aggregate_empty():
    m = aggregate([])
    assert m["total"] == 0 and m["accuracy"] == 0.0
