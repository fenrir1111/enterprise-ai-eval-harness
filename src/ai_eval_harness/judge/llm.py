from __future__ import annotations

import json
import re
from typing import Optional

from ..dataset.models import EvalCase
from .base import Judge
from .deterministic import DeterministicJudge

# 固定 judge 模型 + 固定 prompt 是基线可比性的关键约束（见 docs/limitation.md）。


class LLMJudge(Judge):
    """LLM-as-judge：用 judge 模型对回答打分（0~1）。

    - 仅在安装 litellm 且配置了 api_key 时可用；否则回退确定性打分。
    - 固定 prompt 模板，避免基线漂移。
    - 解析失败时回退到确定性打分，保证评测不中断。
    """

    def __init__(
        self,
        model: str,
        api_base: str = "",
        api_key: str = "",
        prompt: str = "",
        deterministic: Optional[Judge] = None,
    ) -> None:
        self.model = model
        self.api_base = api_base
        self.api_key = api_key
        self.prompt = prompt
        # 未显式指定时，回退到确定性判分，保证离线/不可用也能出分
        self.deterministic = deterministic or DeterministicJudge()

    @property
    def available(self) -> bool:
        try:
            import litellm  # noqa: F401

            return bool(self.api_key)
        except Exception:
            return False

    def _fallback(self, case: EvalCase, prediction: str, status: str) -> tuple[float, str]:
        if self.deterministic is not None:
            return self.deterministic.score(case, prediction, status)
        return 0.0, "judge unavailable (fallback)"

    def score(self, case: EvalCase, prediction: str, status: str) -> tuple[float, str]:
        if not self.available:
            return self._fallback(case, prediction, status)
        import litellm

        template = self.prompt or (
            "你是严格的验收评审。给定【问题】【标准答案】【模型回答】，"
            "判断模型回答是否正确或基本正确（0~1 分）。"
            "只输出 JSON：{\"score\": 0.0, \"reason\": \"...\"}"
        )
        user = (
            f"【问题】{case.question}\n"
            f"【标准答案】{case.golden_answer or '（拒答）'}\n"
            f"【模型回答】{prediction or '（空）'}\n"
        )
        try:
            resp = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": template},
                    {"role": "user", "content": user},
                ],
                base_url=self.api_base or None,
                api_key=self.api_key or None,
                temperature=0,
                max_tokens=160,
            )
            text = resp.choices[0].message.content or ""
            m = re.search(r"\{.*\}", text, re.DOTALL)
            obj = json.loads(m.group(0)) if m else {}
            score = float(obj.get("score", 0.0))
            score = max(0.0, min(1.0, score))
            return score, str(obj.get("reason", ""))
        except Exception as e:  # noqa: BLE001
            return self._fallback(case, prediction, str(e))
