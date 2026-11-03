# 架构｜enterprise-ai-eval-harness

## 总体链路
```
评测数据集(JSON)
   → 任务分发（按场景 rag/sql/agent 过滤）
   → 目标服务适配器（TargetService.answer）
   → 确定性判分（数值/文本/拒答）+ 可选 LLM-as-judge
   → 指标聚合（准确率/拒答率/误拒/漏拒/召回…）
   → badcase 归档（JSONL）+ 报表导出（Markdown/CSV）
   → 版本对比（base vs candidate）
```

## 模块划分
| 模块 | 职责 |
|---|---|
| `dataset` | 评测用例/数据集模型与 JSON 读写 |
| `metrics` | 文本归一化、数字提取、关键片段召回率、确定性判分、指标聚合 |
| `judge` | 打分器抽象：确定性判分（默认）、LLM-as-judge（可选 litellm） |
| `runner` | 目标服务抽象与模拟服务、评测执行器、版本对比、内置服务预设 |
| `report` | Markdown 验收报表、版本对比报表、CSV/JSONL 导出 |
| `audit` | 评测任务审计（JSONL + 内存环形缓冲） |
| `main` | FastAPI 接口 + Harness 门面 |
| `streamlit_app` | 可视化后台（跑评测 / 版本对比 / 评测集 / badcase） |

## 关键设计
- **确定性优先**：默认走确定性判分（数值容差 / 文本归一化 / 拒答判定），离线、可复现、可单测；
  LLM-as-judge 作为可选增强，未配置或解析失败自动回退，保证评测不中断。
- **客观指标与主观打分分离**：业务准确率、拒答/误拒/漏拒为客观可算指标；judge 均分为 LLM 主观指标，分开展示。
- **基线可比性**：固定 judge 模型 + 固定打分 prompt（见 `config.judge_prompt`），避免换裁判导致基线漂移。
- **合规风险单列**：`expect_refuse` 用例用于校验「该拒答的必须拒答」（漏拒）与「不该拒答的不乱拒」（误拒），
  越权/敏感场景的漏拒会被单列为风险，而不是简单算进准确率。

## 与 semantic-sql-guard 联动
把 semantic-sql-guard 的 `/ask` 接口封装成 `TargetService`（见 `examples/adapter_example.py`），
即可用它跑 Text2SQL 准确率与漏拒评测，失败 case 自动回流。
