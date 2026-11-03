from __future__ import annotations

from .evaluator import EvalRun


def compare_runs(base: EvalRun, candidate: EvalRun) -> dict:
    """版本对比：candidate 相对 base 的指标变化 + 变好/变差用例。

    仅对“两次都出现的用例”做逐条对比，避免评测集不一致带来的噪声。
    """
    base_map = {r.case.id: r for r in base.results}
    cand_map = {r.case.id: r for r in candidate.results}
    common = [i for i in base_map if i in cand_map]

    improved, regressed = [], []
    for cid in common:
        b, c = base_map[cid], cand_map[cid]
        if c.correct and not b.correct:
            improved.append(cid)
        elif b.correct and not c.correct:
            regressed.append(cid)

    metric_delta = {}
    for k, v in candidate.metrics.items():
        if isinstance(v, (int, float)) and isinstance(base.metrics.get(k), (int, float)):
            metric_delta[k] = round(v - base.metrics[k], 4)

    return {
        "base": {"name": base.service_name, "metrics": base.metrics},
        "candidate": {"name": candidate.service_name, "metrics": candidate.metrics},
        "metric_delta": metric_delta,
        "improved_ids": improved,
        "regressed_ids": regressed,
        "improved_count": len(improved),
        "regressed_count": len(regressed),
        "common_cases": len(common),
    }
