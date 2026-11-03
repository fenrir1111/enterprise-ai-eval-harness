"""FastAPI 服务入口。

接口：
- GET  /health     健康检查
- GET  /services   可用的模拟目标服务
- GET  /dataset    评测集概览
- POST /evaluate   对指定服务跑一次评测 → 指标 + 报表 + badcase
- POST /compare    版本对比（base vs candidate）
- POST /export     导出最近一次评测的 Markdown / CSV / badcase JSONL
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .audit import AuditLogger
from .config import get_settings
from .dataset import load_dataset
from .judge.base import Judge
from .judge.deterministic import DeterministicJudge
from .judge.llm import LLMJudge
from .report.export import (
    export_badcase_jsonl,
    export_compare_markdown,
    export_markdown,
    export_results_csv,
)
from .runner.compare import compare_runs
from .runner.evaluator import EvalRun, Evaluator
from .runner.presets import build_services


class EvaluateRequest(BaseModel):
    service: str = Field("rag-v1", description="目标服务名（见 /services）")
    scenarios: Optional[list[str]] = Field(
        None, description="仅评测指定场景，如 ['rag']；缺省为全部"
    )


class CompareRequest(BaseModel):
    base: str = Field("rag-v0")
    candidate: str = Field("rag-v1")


class ExportRequest(BaseModel):
    service: str = Field("rag-v1")
    format: str = Field("markdown", description="markdown | csv | badcase")


def _make_judge() -> Optional[Judge]:
    s = get_settings()
    if not s.judge_enabled:
        return None
    return LLMJudge(
        model=s.judge_model,
        api_base=s.judge_api_base,
        api_key=s.judge_api_key,
        prompt=s.judge_prompt,
        deterministic=DeterministicJudge(),
    )


class Harness:
    """评测基座门面：持有数据集、服务、judge 与最近一次运行结果。"""

    def __init__(self) -> None:
        s = get_settings()
        self.dataset = load_dataset(s.dataset_path)
        self.services = build_services()
        self.judge = _make_judge()
        self.audit = AuditLogger(path=s.badcase_path)
        self.last_run: Optional[EvalRun] = None
        self.report_dir = s.report_dir

    def evaluate(self, service: str, scenarios: Optional[list[str]] = None) -> EvalRun:
        if service not in self.services:
            raise KeyError(f"unknown service: {service}")
        ds = self.dataset
        if scenarios:
            from .dataset.models import EvalDataset

            kept = [c for c in ds.cases if c.scenario in scenarios]
            ds = EvalDataset(ds.name, ds.version, kept)
        run = Evaluator(judge=self.judge).run(ds, self.services[service])
        self.last_run = run
        self.audit.record(
            {
                "service": service,
                "dataset": ds.name,
                "metrics": run.metrics,
                "badcase_count": len(run.badcases),
            }
        )
        return run


def build_app(harness: Optional[Harness] = None) -> FastAPI:
    h = harness or Harness()

    app = FastAPI(
        title="enterprise-ai-eval-harness",
        description="企业 AI 评测基座｜RAG/Text2SQL/Agent 统一回归评测、LLM-as-judge、版本对比、验收报表",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "cases": len(h.dataset.cases), "services": list(h.services)}

    @app.get("/services")
    def services() -> list[dict]:
        return [{"name": n} for n in h.services]

    @app.get("/dataset")
    def dataset() -> dict:
        by: dict[str, int] = {}
        for c in h.dataset.cases:
            by[c.scenario] = by.get(c.scenario, 0) + 1
        return {
            "name": h.dataset.name,
            "version": h.dataset.version,
            "total": len(h.dataset.cases),
            "by_scenario": by,
        }

    @app.post("/evaluate")
    def evaluate(req: EvaluateRequest) -> dict:
        try:
            run = h.evaluate(req.service, req.scenarios)
        except KeyError as e:
            return {"error": str(e)}
        return {
            "metrics": run.metrics,
            "badcase_count": len(run.badcases),
            "report_md": export_markdown(run),
        }

    @app.post("/compare")
    def compare(req: CompareRequest) -> dict:
        base = h.evaluate(req.base)
        cand = h.evaluate(req.candidate)
        return compare_runs(base, cand)

    @app.post("/export")
    def export(req: ExportRequest) -> dict:
        try:
            run = h.evaluate(req.service)
        except KeyError as e:
            return {"error": str(e)}
        if req.format == "csv":
            path = export_results_csv(run, f"{h.report_dir}/{req.service}.csv")
        elif req.format == "badcase":
            path = export_badcase_jsonl(run, f"{h.report_dir}/{req.service}_badcase.jsonl")
        else:
            path = f"{h.report_dir}/{req.service}.md"
            from pathlib import Path

            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(export_markdown(run), encoding="utf-8")
        return {"format": req.format, "path": path}

    @app.get("/compare-report")
    def compare_report(base: str = "rag-v0", candidate: str = "rag-v1") -> dict:
        cmp = compare_runs(h.evaluate(base), h.evaluate(candidate))
        return {"markdown": export_compare_markdown(cmp), "data": cmp}

    return app


app = build_app()
