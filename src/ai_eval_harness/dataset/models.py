from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalCase:
    """一条评测用例。

    scenario: rag | sql | agent，决定可用的指标与 judge 方式。
    golden_answer: 标准答案（RAG/agent 文本，或 SQL 期望数值/文本）。
    expected_sql:  Text2SQL 场景下的期望 SQL（可选，用于语法/等价校验）。
    expect_refuse: 期望被拒答的问题（越权 / 未注册等），服务应返回拒绝。
    tags / risk_tags / scenario: 用于 badcase 检索与分维度统计。
    """

    id: str
    question: str
    scenario: str = "rag"
    golden_answer: str = ""
    expected_sql: Optional[str] = None
    expect_refuse: bool = False
    tags: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "scenario": self.scenario,
            "golden_answer": self.golden_answer,
            "expected_sql": self.expected_sql,
            "expect_refuse": self.expect_refuse,
            "tags": self.tags,
            "risk_tags": self.risk_tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvalCase":
        return cls(
            id=str(d["id"]),
            question=d.get("question", ""),
            scenario=d.get("scenario", "rag"),
            golden_answer=d.get("golden_answer", ""),
            expected_sql=d.get("expected_sql"),
            expect_refuse=bool(d.get("expect_refuse", False)),
            tags=list(d.get("tags", [])),
            risk_tags=list(d.get("risk_tags", [])),
        )


@dataclass
class EvalDataset:
    name: str
    version: str
    cases: list[EvalCase] = field(default_factory=list)

    def by_scenario(self, scenario: str) -> list[EvalCase]:
        return [c for c in self.cases if c.scenario == scenario]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "cases": [c.to_dict() for c in self.cases],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvalDataset":
        return cls(
            name=d.get("name", "unnamed"),
            version=d.get("version", "0.0.0"),
            cases=[EvalCase.from_dict(c) for c in d.get("cases", [])],
        )
