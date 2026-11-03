from __future__ import annotations

from ..dataset.models import EvalCase
from .base import Judge


class DeterministicJudge(Judge):
    """确定性打分：复用 metrics 的确定性判分，score 取 0/1。

    默认使用，保证离线、无 LLM 时评测可复现。
    """

    def score(self, case: EvalCase, prediction: str, status: str) -> tuple[float, str]:
        from ..metrics.core import deterministic_match

        correct, recall, reason = deterministic_match(case, prediction, status)
        return (1.0 if correct else recall * 0.5), reason
