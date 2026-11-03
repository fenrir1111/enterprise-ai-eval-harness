from __future__ import annotations

from abc import ABC, abstractmethod

from ..dataset.models import EvalCase


class Judge(ABC):
    """打分器抽象：给定一条用例与预测，返回 (score 0~1, reason)。"""

    @abstractmethod
    def score(self, case: EvalCase, prediction: str, status: str) -> tuple[float, str]:
        ...
