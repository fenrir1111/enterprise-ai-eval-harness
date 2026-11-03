from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceResult:
    """目标服务一次调用的结果。"""

    answer: str = ""
    refused: bool = False
    ok: bool = True
    error: str = ""
    elapsed_ms: float = 0.0


class TargetService(ABC):
    """被评测的目标服务抽象（RAG / Text2SQL / Agent 均实现此接口）。"""

    name: str = "target"

    @abstractmethod
    def answer(self, question: str) -> ServiceResult:
        ...


class MockService(TargetService):
    """确定性模拟服务：用于 POC 演示与离线测试，无需真实模型。

    rules: {问题子串: (回答, 是否拒答)}，按“最长命中优先”匹配；
    未命中时返回空回答（视为“答不出”），可用来模拟漏答。
    支持模拟超时（timeout_after_ms）与错误（always_error）。
    """

    def __init__(
        self,
        rules: Optional[dict[str, tuple[str, bool]]] = None,
        name: str = "mock",
        timeout_after_ms: float = 0.0,
        always_error: bool = False,
    ) -> None:
        self.rules = rules or {}
        self.name = name
        self.timeout_after_ms = timeout_after_ms
        self.always_error = always_error

    def _match(self, question: str) -> Optional[tuple[str, bool]]:
        best: Optional[tuple[str, bool]] = None
        best_len = -1
        for key, val in self.rules.items():
            if key in question and len(key) > best_len:
                best, best_len = val, len(key)
        return best

    def answer(self, question: str) -> ServiceResult:
        start = time.perf_counter()
        if self.always_error:
            return ServiceResult(ok=False, error="simulated error", elapsed_ms=_ms(start))
        hit = self._match(question)
        if hit is None:
            return ServiceResult(answer="", refused=False, elapsed_ms=_ms(start))
        answer, refused = hit
        return ServiceResult(answer=answer, refused=refused, elapsed_ms=_ms(start))


def _ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000
