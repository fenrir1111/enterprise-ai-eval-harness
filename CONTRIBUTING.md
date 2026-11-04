# 贡献指南 · enterprise-ai-eval-harness

感谢你愿意参与这个项目。这个仓库解决的是 B 端 AI 交付里最容易被忽略的一环：
**上线之后，怎么说得清效果是好是坏，怎么给客户一个能签字的验收结论。**

所以任何改动，都要先回答：**这个改动会不会让评测结果变得更不可信？**

## 快速开始

```bash
git clone https://github.com/fenrir1111/enterprise-ai-eval-harness.git
cd enterprise-ai-eval-harness

uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -e .

.venv/bin/python -m ai_eval_harness.demo    # 全链路 demo（评测 + 版本对比 + badcase）
.venv/bin/python -m pytest -q                 # 跑测试
.venv/bin/python -m uvicorn ai_eval_harness.main:app --port 8000
```

## 提交前必做

```bash
.venv/bin/python -m pytest -q --basetemp="$PWD/.pytest-tmp"   # 必须全绿
.venv/bin/python -m ai_eval_harness.demo                       # 必须退出码 0
```

CI 会自动跑上面两步，再加 FastAPI `/health` 与 Streamlit 控制台冒烟（Python 3.10 / 3.12 双版本）。

## 哪些改动受欢迎

| 类型 | 例子 |
|---|---|
| 新增评测指标 | 忠实度、有害性、成本/延迟指标、格式合规率 |
| 接入新目标服务 | 新的服务适配器（把评测样本转成目标服务调用） |
| 行业评测集 | 金融、政务、客服等场景的样本集与标注规范 |
| 判分器增强 | 新的确定性判分规则、可插拔的 judge 策略 |
| 报表增强 | 新增导出格式、图表、对比维度 |

## 哪些改动不会被接受

- **把客观指标和 judge 打分混在一起呈现的**：两者的可信度不同，必须分离展示
- **让评测结果不可复现的**：同一份评测集 + 同一个版本，结果必须稳定
- **隐藏「漏拒」这类合规风险指标的**：漏拒（该拒的没拒）在 B 端是合规问题，不是普通指标
- **在核心链路里强依赖 LLM**：默认判分必须确定性；judge 是可选增强

## 代码约定

- **Python ≥3.10**，`from __future__ import annotations` 开头，类型标注齐全
- **行宽 100 以内**，命名 `snake_case`，公开 API 用 docstring 说明「为什么」
- **相对导入用绝对导入**：`streamlit_app.py` 会被 Streamlit 当独立脚本执行，
  相对导入会直接 `ImportError` —— 统一写成 `from ai_eval_harness.xxx import ...`。
  **包括 `if` 分支 / 函数里的延迟导入** —— 那类 bug 首屏正常，只有用户点到该分支才炸，
  AppTest 初始渲染和 HTTP 200 都看不出来。`tests/test_streamlit_app.py` 用 AST 全量扫描 +
  点击主按钮的交互冒烟，在 CI 里守住这条。
- **新指标必须带单元测试**：至少包含「完美预测」与「完全失败」两个边界用例
- **评测集变更要说明标注依据**：新增/修改样本请在 PR 描述里写清标注口径

## 提交信息

```
feat: 新增忠实度指标（基于标准答案的 token 级召回）
fix: 修复 judge 打分为 0 时被当作「未参与评测」的问题
docs: 补充评测集标注规范
```

## Issue

提 Issue 时请尽量带上：

1. 复现步骤或最小样例
2. 期望行为 vs 实际行为
3. 运行环境（Python 版本、目标服务类型）
4. 相关评测输出片段（**注意脱敏**）

## 致谢

有效贡献会在 README 的致谢栏署名。

## License

贡献即视为同意以 MIT 协议授权你的改动。
