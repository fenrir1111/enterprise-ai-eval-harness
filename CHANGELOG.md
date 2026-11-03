# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 与语义化版本。

## [0.1.0] - 2026-11-03

### Added
- 评测集管理：`EvalCase` / `EvalDataset` 模型，JSON 读写（question、golden 答案、约束/风险标签、场景标签）。
- 多维指标：业务准确率、拒答率、误拒率、漏拒率（合规风险）、超时率、异常率、答案召回率。
- 确定性判分：数值容差 / 文本归一化 / 关键片段召回 / 拒答判定，离线可复现。
- LLM-as-judge（litellm，可选）：固定 prompt 模板，未配置或解析失败自动回退确定性打分。
- 版本对比：`compare_runs` 输出指标差异 + 变好/变差用例。
- Badcase 自动归档：失败/风险样本打标，导出 JSONL。
- 报表导出：Markdown 验收报表、版本对比报表、CSV（可 Excel 打开）。
- FastAPI 接口：`/evaluate`、`/compare`、`/export`、`/compare-report`、`/dataset`、`/services`、`/health`。
- 内置模拟目标服务（rag-v0 / rag-v1 / sql-guard / agent）用于演示与离线测试。
- 全链路 demo（`make demo`）与 pytest 测试。
- 工程化：`Makefile`、`Dockerfile`、`docker-compose.yml`、`.env.example`、PRD / architecture / limitation 文档、样例评测集、Streamlit 可视化后台。

> 说明：当前为 v0 版本，定位 POC / 试点交付辅助底座，**不建议不经评估直接上核心生产**。

## [0.0.1] - 2026-11-03
### Planned
- v0.2：批量版本对比报表、标签体系、评测集批量导入
- v0.3：Webhook 对接 CI，自动回归评测
- v0.4：社区共享评测集市场
