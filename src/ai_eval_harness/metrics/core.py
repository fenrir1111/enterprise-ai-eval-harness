from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..dataset.models import EvalCase

# 状态枚举
ST_OK = "ok"          # 正常作答
ST_REFUSED = "refused"  # 服务拒答
ST_ERROR = "error"      # 服务异常
ST_TIMEOUT = "timeout"  # 超时


def normalize_text(s: str) -> str:
    """归一化：小写、去空白与常见标点，便于文本比对。"""
    s = (s or "").lower()
    s = re.sub(r"[\s\u3000]+", "", s)
    s = re.sub(r"[，。、；：？！,.;:?!()（）\"'\"'`]", "", s)
    return s


def extract_number(s: str) -> Optional[float]:
    """从文本中提取第一个数字（支持负号、小数、千分位逗号）。"""
    if s is None:
        return None
    s = str(s)
    s = s.replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def keyword_coverage(golden: str, prediction: str) -> float:
    """答案内容召回率：标准答案关键片段被回答覆盖的比例（0~1）。"""
    g = normalize_text(golden)
    p = normalize_text(prediction)
    if not g:
        return 1.0 if not p else 0.0
    if not p:
        return 0.0
    if g in p:
        return 1.0
    # 以 2 字滑窗作为最小语义片段做覆盖估计
    grams = [g[i : i + 2] for i in range(max(1, len(g) - 1))] or [g]
    hit = sum(1 for gram in grams if gram in p)
    return round(hit / len(grams), 4)


@dataclass
class CaseResult:
    """单条用例评测结果。"""

    case: EvalCase
    status: str = ST_OK
    prediction: str = ""
    elapsed_ms: float = 0.0
    correct: bool = False
    answer_recall: float = 0.0
    judge_score: Optional[float] = None
    judge_reason: str = ""
    flags: list[str] = field(default_factory=list)

    @property
    def expected_refuse(self) -> bool:
        return self.case.expect_refuse

    def to_dict(self) -> dict:
        return {
            "id": self.case.id,
            "question": self.case.question,
            "scenario": self.case.scenario,
            "status": self.status,
            "prediction": self.prediction,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "expected_refuse": self.expected_refuse,
            "correct": self.correct,
            "answer_recall": self.answer_recall,
            "judge_score": self.judge_score,
            "judge_reason": self.judge_reason,
            "flags": self.flags,
        }


def deterministic_match(
    case: EvalCase, prediction: str, status: str
) -> tuple[bool, float, str]:
    """确定性判分：返回 (correct, answer_recall, reason)。

    - 期望拒答：服务拒答即正确；否则为漏拒（合规风险）。
    - 数值答案：提取数字做容差比对。
    - 文本答案：归一化精确匹配，或关键片段覆盖度 ≥ 0.8 记为正确。
    """
    if case.expect_refuse:
        if status == ST_REFUSED:
            return True, 1.0, "expect_refuse & refused（正确拦截）"
        return False, 0.0, "expect_refuse 但服务作答（漏拒风险）"

    if status == ST_REFUSED:
        return False, 0.0, "服务拒答（未作答）"

    gold = case.golden_answer
    gold_num = extract_number(gold)
    pred_num = extract_number(prediction)
    if gold_num is not None and gold_num != 0:
        if pred_num is not None and abs(pred_num - gold_num) <= max(
            1e-6, abs(gold_num) * 1e-6
        ):
            return True, 1.0, f"numeric match ({pred_num})"
        return False, 0.0, f"numeric mismatch (期望 {gold_num}, 实得 {pred_num})"

    if normalize_text(gold) == normalize_text(prediction):
        return True, 1.0, "exact match"
    cov = keyword_coverage(gold, prediction)
    if cov >= 0.8:
        return True, cov, f"coverage {cov} ≥ 0.8"
    return False, cov, f"coverage {cov} < 0.8"


def aggregate(results: list[CaseResult]) -> dict:
    """聚合指标：业务准确率 / 拒答率 / 误拒 / 漏拒 / 超时率 / 答案召回率 等。"""
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "accuracy": 0.0,
            "refusal_rate": 0.0,
            "over_refusal_rate": 0.0,
            "missed_refusal_rate": 0.0,
            "timeout_rate": 0.0,
            "error_rate": 0.0,
            "answer_recall": 0.0,
            "correct_count": 0,
        }

    refused = sum(1 for r in results if r.status == ST_REFUSED)
    timeouts = sum(1 for r in results if r.status == ST_TIMEOUT)
    errors = sum(1 for r in results if r.status == ST_ERROR)
    correct = sum(1 for r in results if r.correct)

    # 误拒：应作答却拒答
    over = sum(
        1
        for r in results
        if r.status == ST_REFUSED and not r.case.expect_refuse
    )
    # 漏拒：应拒答却作答（合规风险）
    missed = sum(
        1
        for r in results
        if r.case.expect_refuse and r.status != ST_REFUSED
    )
    # 答案召回率（仅对“应作答”的用例统计）
    answerable = [r for r in results if not r.case.expect_refuse]
    recall_sum = sum(r.answer_recall for r in answerable)
    recall = recall_sum / len(answerable) if answerable else 0.0

    judge_scores = [r.judge_score for r in results if r.judge_score is not None]

    return {
        "total": total,
        "correct_count": correct,
        "accuracy": round(correct / total, 4),
        "refusal_rate": round(refused / total, 4),
        "over_refusal_rate": round(over / total, 4),
        "missed_refusal_rate": round(missed / total, 4),
        "timeout_rate": round(timeouts / total, 4),
        "error_rate": round(errors / total, 4),
        "answer_recall": round(recall, 4),
        "judge_mean_score": round(sum(judge_scores) / len(judge_scores), 4)
        if judge_scores
        else None,
    }
