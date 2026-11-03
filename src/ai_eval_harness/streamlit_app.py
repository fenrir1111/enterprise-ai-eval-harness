"""Streamlit 可视化评测后台。

启动： uv run streamlit run src/ai_eval_harness/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit 以「独立脚本」方式执行本文件（无 __package__），相对导入会直接 ImportError。
# 这里把 src/ 加入 sys.path 并改用绝对导入，保证「clone 即跑」和「已安装」两种场景都能启动。
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ai_eval_harness.config import get_settings  # noqa: E402
from ai_eval_harness.dataset import load_dataset  # noqa: E402
from ai_eval_harness.judge.deterministic import DeterministicJudge  # noqa: E402
from ai_eval_harness.report.export import (  # noqa: E402
    export_compare_markdown,
    export_markdown,
)
from ai_eval_harness.runner.compare import compare_runs  # noqa: E402
from ai_eval_harness.runner.evaluator import Evaluator  # noqa: E402
from ai_eval_harness.runner.presets import build_services  # noqa: E402


@st.cache_resource
def _harness():
    s = get_settings()
    dataset = load_dataset(s.dataset_path)
    services = build_services()
    judge = DeterministicJudge()
    return {"dataset": dataset, "services": services, "judge": judge}


st.set_page_config(page_title="AI 评测基座", layout="wide")
h = _harness()
st.title("enterprise-ai-eval-harness｜企业 AI 评测基座")
st.caption("RAG / Text2SQL / Agent 统一回归评测 · LLM-as-judge · 版本对比 · badcase 归档 · 验收报表")

tab_run, tab_cmp, tab_data, tab_bad = st.tabs(
    ["① 跑评测", "② 版本对比", "③ 评测集", "④ Badcase & 报表"]
)

with tab_run:
    col1, col2 = st.columns([1, 1])
    with col1:
        service = st.selectbox("目标服务", list(h["services"].keys()), index=1)
        scenarios = st.multiselect("场景（缺省=全部）", ["rag", "sql", "agent"])
        go = st.button("▶ 开始评测", type="primary")
    if go and st.session_state.get("_run_svc") != service:
        ds = h["dataset"]
        if scenarios:
            from .dataset.models import EvalDataset

            ds = EvalDataset(ds.name, ds.version, [c for c in ds.cases if c.scenario in scenarios])
        run = Evaluator(judge=h["judge"]).run(ds, h["services"][service])
        st.session_state["run"] = run
    run = st.session_state.get("run")
    if run:
        with col2:
            m = run.metrics
            c1, c2 = st.columns(2)
            c1.metric("业务准确率", f"{m.get('accuracy', 0):.2%}")
            c2.metric("拒答率", f"{m.get('refusal_rate', 0):.2%}")
            c3, c4 = st.columns(2)
            c3.metric("误拒率", f"{m.get('over_refusal_rate', 0):.2%}")
            c4.metric("漏拒率(合规风险)", f"{m.get('missed_refusal_rate', 0):.2%}")
        st.markdown("#### 验收报表")
        st.markdown(export_markdown(run))

with tab_cmp:
    c1, c2 = st.columns(2)
    base = c1.selectbox("基线版本", list(h["services"].keys()), index=0)
    cand = c2.selectbox("候选版本", list(h["services"].keys()), index=1)
    if st.button("对比版本"):
        cmp = compare_runs(
            Evaluator(judge=h["judge"]).run(h["dataset"], h["services"][base]),
            Evaluator(judge=h["judge"]).run(h["dataset"], h["services"][cand]),
        )
        st.session_state["cmp"] = cmp
    cmp = st.session_state.get("cmp")
    if cmp:
        st.markdown(export_compare_markdown(cmp))

with tab_data:
    st.subheader(f"评测集：{h['dataset'].name} v{h['dataset'].version}")
    rows = [
        {
            "id": c.id,
            "question": c.question,
            "scenario": c.scenario,
            "golden": c.golden_answer or "(拒答)",
            "expect_refuse": c.expect_refuse,
            "risk": ",".join(c.risk_tags) or "-",
        }
        for c in h["dataset"].cases
    ]
    st.dataframe(rows, hide_index=True)

with tab_bad:
    run = st.session_state.get("run")
    if run:
        if run.badcases:
            st.dataframe(run.badcases, hide_index=True)
        else:
            st.success("无失败 / 风险样本。")
        st.download_button(
            "下载 Markdown 报表", export_markdown(run), mime="text/markdown"
        )
    else:
        st.info("请先在「① 跑评测」中运行一次评测。")
