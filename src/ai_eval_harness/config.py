from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，支持 .env / 环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 评测集 / badcase / 报告路径
    dataset_path: str = "./data/sample_eval.json"
    badcase_path: str = "./data/badcase.jsonl"
    report_dir: str = "./data/reports"

    # 可选 Judge LLM（LLM-as-judge，不装 litellm 时走确定性打分）
    judge_enabled: bool = False
    judge_model: str = "gpt-4o-mini"
    judge_api_base: str = ""
    judge_api_key: str = ""
    # 固定打分 prompt 模板（基线可比性的关键约束）
    judge_prompt: str = (
        "你是严格的验收评审。给定【问题】【标准答案】【模型回答】，"
        "判断模型回答是否正确或基本正确（0~1 分）。"
        "只输出 JSON：{\"score\": 0.0, \"reason\": \"...\"}"
    )

    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
