"""全链路 demo：无需起服务，直接跑评测 + 版本对比 + badcase 归档。

运行： uv run python -m ai_eval_harness.demo
覆盖：对 rag-v0 / rag-v1 评测、指标聚合、版本对比、badcase 收集。
"""

from __future__ import annotations

from .audit import AuditLogger
from .config import get_settings
from .dataset import load_dataset
from .judge.deterministic import DeterministicJudge
from .report.export import export_badcase_jsonl, export_compare_markdown, export_markdown
from .runner.compare import compare_runs
from .runner.evaluator import Evaluator
from .runner.presets import build_mock_rag_v0, build_mock_rag_v1


def main() -> None:
    s = get_settings()
    dataset = load_dataset(s.dataset_path)
    judge = DeterministicJudge()

    print("=" * 72)
    print("enterprise-ai-eval-harness 全链路 demo")
    print("=" * 72)

    run_v0 = Evaluator(judge=judge).run(dataset, build_mock_rag_v0())
    run_v1 = Evaluator(judge=judge).run(dataset, build_mock_rag_v1())

    print("-" * 72)
    print("【RAG v0 评测指标】")
    for k, v in run_v0.metrics.items():
        print(f"  {k:>18}: {v}")
    print("-" * 72)
    print("【RAG v1 评测指标】")
    for k, v in run_v1.metrics.items():
        print(f"  {k:>18}: {v}")

    cmp = compare_runs(run_v0, run_v1)
    print("-" * 72)
    print("【版本对比 v0 → v1】")
    print(f"  变好 {cmp['improved_count']} 条：{cmp['improved_ids']}")
    print(f"  变差 {cmp['regressed_count']} 条：{cmp['regressed_ids']}")
    for k, delta in cmp["metric_delta"].items():
        sign = "+" if delta > 0 else ""
        print(f"  {k:>18}: {sign}{delta}")

    print("-" * 72)
    print("【v0 Badcase 明细】")
    for b in run_v0.badcases:
        print(f"  [{b['id']}] {b['question']} → {'；'.join(b['reasons'])}")

    print("=" * 72)
    print("Markdown 验收报表（节选）：")
    print(export_markdown(run_v1).split("## Badcase 明细")[0].rstrip())
    print("=" * 72)

    bc_path = export_badcase_jsonl(run_v0, "data/reports/rag-v0_badcase.jsonl")
    print(f"badcase 已归档 → {bc_path}")


if __name__ == "__main__":
    main()
