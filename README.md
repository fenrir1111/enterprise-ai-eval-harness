# enterprise-ai-eval-harness
> Enterprise AI Evaluation Harness｜面向 B 端交付的 LLM/RAG/Text2SQL/Agent 统一评测基座

> 属于【enterprise-ai-stack】B端私有化 AI 交付底座合集
> 👉 总入口：https://github.com/fenrir1111/enterprise-ai-stack

## 一句话简介
解决 B 端 AI 交付痛点：**缺少标准化评测流程**，上线后效果漂移、幻觉无法量化、验收无统一指标。
面向 FDE、AI 交付、数据产品团队，开箱即用的自动评测框架：支持 **LLM-as-judge**、批量对比模型版本、
沉淀 badcase 库、自动生成可直接交付客户的验收报表。

## 适用场景
- RAG 知识库召回 & 回答效果验收
- Text2SQL 准确率、漏拒/越权检测
- Agent 任务执行成功率评估
- 版本迭代回归测试、POC 验收材料输出

## 核心能力
1. **评测集管理**：question / golden-answer / 约束标签 / 风险标签 / 场景标签（rag/sql/agent）。
2. **多维度指标**：业务准确率、拒答率、误拒率、**漏拒率（合规风险）**、超时率、异常率、答案召回率。
3. **LLM-as-judge 自动打分**（可选，固定 prompt 模板）；未配置时走**确定性判分**（离线、可复现）。
4. **版本对比**：v0.1 vs v0.2 指标差异 + 变好/变差用例定位。
5. **Badcase 自动归档**：失败/风险样本自动打标，导出 JSONL 给标注团队回流。
6. **报表导出**：Markdown / CSV（可 Excel 打开），直接作为客户验收材料。
7. **Streamlit 可视化后台**，无需写代码即可跑评测、看报表。

## 架构简图
```
评测数据集 → 任务分发（按场景过滤） → 目标服务适配器（RAG/Text2SQL/Agent）
   → 确定性判分 + 可选 LLM-as-judge → 指标聚合 & badcase 归档 → 报表输出 / 版本对比
```

## 快速启动
### 方式一：uv（推荐，本地）
```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -e .

# 跑全链路 demo（无需起服务：评测 + 版本对比 + badcase）
.venv/bin/python -m ai_eval_harness.demo

# 起服务
.venv/bin/python -m uvicorn ai_eval_harness.main:app --host 0.0.0.0 --port 8000
# 交互式文档: http://127.0.0.1:8000/docs
```
或用 `make` 快捷命令：`make demo` / `make run` / `make test` / `make ui`。

### 方式二：Docker
```bash
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

### 调用示例
```bash
# 对内置模拟服务 rag-v1 跑一次全场景评测
curl -s localhost:8000/evaluate -H 'Content-Type: application/json' -d '{"service":"rag-v1"}'

# 仅评测 RAG 场景
curl -s localhost:8000/evaluate -H 'Content-Type: application/json' \
  -d '{"service":"rag-v1","scenarios":["rag"]}'

# 版本对比 rag-v0 → rag-v1
curl -s localhost:8000/compare -H 'Content-Type: application/json' \
  -d '{"base":"rag-v0","candidate":"rag-v1"}'

# 导出 Markdown 验收报表
curl -s localhost:8000/export -H 'Content-Type: application/json' \
  -d '{"service":"rag-v1","format":"markdown"}'
```

## 核心接口
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/evaluate` | 对指定服务跑评测 → 指标 + Markdown 报表 + badcase 数 |
| POST | `/compare` | 版本对比（base vs candidate） |
| POST | `/export` | 导出 Markdown / CSV / badcase JSONL |
| GET | `/compare-report` | 版本对比 Markdown 报表 |
| GET | `/dataset` | 评测集概览 |
| GET | `/services` | 可用模拟目标服务 |
| GET | `/health` | 健康检查 |

## 接入你的真实服务
把 RAG/Text2SQL/Agent 封装成实现 `TargetService.answer(question) -> ServiceResult` 的适配器即可，
示例见 [`examples/adapter_example.py`](examples/adapter_example.py)（封装 semantic-sql-guard 的 `/ask` 接口）。

## 设计原则
- **确定性优先**：默认离线可跑、可复现、可单测；LLM 裁判为可选增强，失败自动回退。
- **客观指标与主观打分分离**：准确率/拒答/漏拒为客观可算指标，judge 均分为主观指标，分开展示。
- **合规风险单列**：越权/敏感场景的「漏拒」单列为风险，而不是简单算进准确率。

## 已知局限（非常重要）
1. **LLM-as-judge 存在主观偏差**，只能作为回归辅助，**不能替代人工抽检**；正式验收须人工抽样复核。
2. 不支持十万级以上超大评测集，面向 POC / 试点回归验收量级。
3. Judge 模型本身会幻觉，**换 judge 会改变基线**；基线必须固定 judge 模型与打分 prompt。
4. 当前优先单轮问答，暂不支持复杂多轮长上下文评测。
5. 无高并发分布式设计，适合内部小团队，不直接上生产高并发。

> 详见 [`docs/limitation.md`](docs/limitation.md)。

## 迭代计划
- v0.1：基础评测、单任务、报表导出、badcase 归档（本仓库当前）
- v0.2：批量版本对比报表、标签体系、评测集批量导入
- v0.3：Webhook 对接 CI，自动回归评测
- v0.4：社区共享评测集市场

## 适合人群
AI 交付 FDE、RAG 产品、Text2SQL 落地团队、大模型中台工程师。

## 参与共建
欢迎提交 Issue（反馈 bug、补充行业评测样例）、PR（新增指标、接入更多目标服务）。有效贡献在 README 致谢栏署名。

## License
MIT License，可自由使用、二次修改、商用；当前为 v0 版本，生产使用请自行评估风险。
