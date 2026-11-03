from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from ..runner.evaluator import EvalRun

_METRIC_LABELS = {
    "total": "用例总数",
    "accuracy": "业务准确率",
    "refusal_rate": "拒答率",
    "over_refusal_rate": "误拒率",
    "missed_refusal_rate": "漏拒率（合规风险）",
    "timeout_rate": "超时率",
    "error_rate": "异常率",
    "answer_recall": "答案召回率",
    "judge_mean_score": "LLM-judge 均分",
    "correct_count": "命中数",
}


def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if v == int(v) else f"{v:.4f}"
    return str(v)


def export_markdown(run: EvalRun) -> str:
    """Markdown 验收报表：指标总览 + 失败/badcase 明细。"""
    m = run.metrics
    lines = [
        "# 验收评测报表",
        "",
        f"- 评测对象：`{run.service_name}`",
        f"- 评测集：`{run.dataset_name}` v{run.dataset_version}",
        f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 指标总览",
        "",
        "| 指标 | 数值 |",
        "|---|---|",
    ]
    for k, label in _METRIC_LABELS.items():
        if k in m:
            lines.append(f"| {label} | {_fmt(m[k])} |")
    lines += [
        "",
        "## Badcase 明细",
        "",
    ]
    if run.badcases:
        lines += [
            "| ID | 问题 | 场景 | 状态 | 是否正确 | 召回 | 原因 |",
            "|---|---|---|---|---|---|---|",
        ]
        for b in run.badcases:
            lines.append(
                f"| {b['id']} | {b['question']} | {b['scenario']} | {b['status']} "
                f"| {'是' if b['correct'] else '否'} | {b['answer_recall']} "
                f"| {'；'.join(b['reasons'])} |"
            )
    else:
        lines.append("无失败 / 风险样本。")
    lines += [
        "",
        "> 说明：LLM-as-judge 存在主观偏差，仅作为回归辅助，"
        "**不能替代人工抽检**，正式验收须人工抽样复核。",
        "",
    ]
    return "\n".join(lines)


def export_compare_markdown(cmp: dict) -> str:
    """版本对比报表：指标增减 + 变好/变差用例。"""
    lines = [
        "# 版本对比报表",
        "",
        f"- 基线：`{cmp['base']['name']}`",
        f"- 候选：`{cmp['candidate']['name']}`",
        f"- 对比用例数：{cmp['common_cases']}",
        "",
        "## 指标变化（candidate − base）",
        "",
        "| 指标 | 基线 | 候选 | 变化 |",
        "|---|---|---|---|",
    ]
    for k, delta in cmp["metric_delta"].items():
        label = _METRIC_LABELS.get(k, k)
        base_v = cmp["base"]["metrics"].get(k)
        cand_v = cmp["candidate"]["metrics"].get(k)
        sign = "+" if delta > 0 else ""
        lines.append(f"| {label} | {_fmt(base_v)} | {_fmt(cand_v)} | {sign}{delta} |")
    lines += ["", f"- 变好用例：{cmp['improved_count']} 条", f"- 变差用例：{cmp['regressed_count']} 条"]
    if cmp["regressed_ids"]:
        lines += ["", "### 变差用例 ID", ""] + [f"- {i}" for i in cmp["regressed_ids"]]
    lines.append("")
    return "\n".join(lines)


def export_results_csv(run: EvalRun, path: str) -> str:
    """逐条结果导出 CSV（可被 Excel 打开）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "id", "question", "scenario", "status", "prediction",
                "expected_refuse", "correct", "answer_recall",
                "judge_score", "flags",
            ]
        )
        for r in run.results:
            w.writerow(
                [
                    r.case.id,
                    r.case.question,
                    r.case.scenario,
                    r.status,
                    r.prediction,
                    r.expected_refuse,
                    r.correct,
                    r.answer_recall,
                    r.judge_score if r.judge_score is not None else "",
                    ";".join(r.flags),
                ]
            )
    return str(p)


def export_badcase_jsonl(run: EvalRun, path: str) -> str:
    """badcase 归档为 JSONL（供标注团队回流）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for b in run.badcases:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    return str(p)
