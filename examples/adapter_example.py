"""如何把你真实的 RAG / Text2SQL / Agent 服务接进评测基座。

只需实现 `TargetService.answer(question) -> ServiceResult` 一个方法。
下面的例子把 semantic-sql-guard 的 HTTP 接口封装成被评测目标。
"""

from __future__ import annotations

import httpx

from ai_eval_harness.runner.services import ServiceResult, TargetService

# 目标服务地址（semantic-sql-guard 起在 8000）
BASE_URL = "http://127.0.0.1:8000"


class SemanticSqlGuardService(TargetService):
    name = "semantic-sql-guard"

    def answer(self, question: str) -> ServiceResult:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{BASE_URL}/ask",
                    json={"question": question, "role": "national"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:  # noqa: BLE001
            return ServiceResult(ok=False, error=str(e))

        # semantic-sql-guard 返回 status / answer
        refused = data.get("status") in ("blocked", "rejected")
        return ServiceResult(
            answer=data.get("answer", ""),
            refused=refused,
            ok=True,
        )


if __name__ == "__main__":
    from ai_eval_harness.dataset import load_dataset
    from ai_eval_harness.judge.deterministic import DeterministicJudge
    from ai_eval_harness.runner.evaluator import Evaluator

    svc = SemanticSqlGuardService()
    ds = load_dataset("data/sample_eval.json")
    ds = type(ds)(ds.name, ds.version, [c for c in ds.cases if c.scenario == "sql"])
    run = Evaluator(judge=DeterministicJudge()).run(ds, svc)
    print(run.metrics)
