import json
from pathlib import Path

from ai_eval_harness.judge.deterministic import DeterministicJudge
from ai_eval_harness.report.export import (
    export_badcase_jsonl,
    export_compare_markdown,
    export_markdown,
    export_results_csv,
)
from ai_eval_harness.runner.compare import compare_runs
from ai_eval_harness.runner.evaluator import Evaluator


def test_export_markdown_contains_metrics(sample_dataset, rag_v1):
    run = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v1)
    md = export_markdown(run)
    assert "验收评测报表" in md
    assert "业务准确率" in md
    assert "rag-v1" in md


def test_export_csv(tmp_path, sample_dataset, rag_v1):
    run = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v1)
    path = export_results_csv(run, str(tmp_path / "r.csv"))
    p = Path(path)
    assert p.exists()
    lines = p.read_text(encoding="utf-8-sig").strip().splitlines()
    assert len(lines) == 1 + len(run.results)  # 表头 + 每行
    assert "question" in lines[0]


def test_export_badcase_jsonl(tmp_path, sample_dataset, rag_v0):
    run = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v0)
    path = export_badcase_jsonl(run, str(tmp_path / "b.jsonl"))
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(run.badcases)
    obj = json.loads(lines[0])
    assert "reasons" in obj


def test_export_compare_markdown(sample_dataset, rag_v0, rag_v1):
    base = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v0)
    cand = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v1)
    cmp = compare_runs(base, cand)
    md = export_compare_markdown(cmp)
    assert "版本对比报表" in md
    assert "rag-v1" in md
