from ai_eval_harness.judge.deterministic import DeterministicJudge
from ai_eval_harness.runner.compare import compare_runs
from ai_eval_harness.runner.evaluator import Evaluator


def test_compare_detects_improvement(sample_dataset, rag_v0, rag_v1):
    base = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v0)
    cand = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v1)
    cmp = compare_runs(base, cand)
    # rag-v1 补齐“涉密”回答 + “域外”正确拒答 → 至少这两条变好
    assert cmp["improved_count"] >= 2
    assert "rag-003" in cmp["improved_ids"]
    assert "rag-004" in cmp["improved_ids"]
    # 准确率应不降
    assert cmp["candidate"]["metrics"]["accuracy"] >= base.metrics["accuracy"]


def test_compare_metric_delta_keys(sample_dataset, rag_v0, rag_v1):
    base = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v0)
    cand = Evaluator(judge=DeterministicJudge()).run(sample_dataset, rag_v1)
    cmp = compare_runs(base, cand)
    assert "accuracy" in cmp["metric_delta"]
    assert cmp["common_cases"] == len(sample_dataset.cases)
