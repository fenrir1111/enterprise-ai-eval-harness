from __future__ import annotations

import json
from pathlib import Path

from .models import EvalDataset


def load_dataset(path: str) -> EvalDataset:
    """加载评测集（JSON）。文件不存在时返回空数据集，避免 POC 冷启动报错。"""
    p = Path(path)
    if not p.exists():
        return EvalDataset(name="empty", version="0.0.0", cases=[])
    data = json.loads(p.read_text(encoding="utf-8"))
    return EvalDataset.from_dict(data)


def save_dataset(ds: EvalDataset, path: str) -> None:
    """保存评测集（JSON）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(ds.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
