from ai_eval_harness.dataset.registry import load_dataset, save_dataset
from ai_eval_harness.dataset.models import EvalDataset, EvalCase


def test_save_and_load_roundtrip(tmp_path):
    ds = EvalDataset(name="d", version="1.0.0", cases=[
        EvalCase(id="a", question="q", golden_answer="ans", scenario="rag",
                 tags=["t"], risk_tags=["r"], expect_refuse=False),
    ])
    path = str(tmp_path / "ds.json")
    save_dataset(ds, path)
    loaded = load_dataset(path)
    assert loaded.name == "d"
    assert loaded.version == "1.0.0"
    assert len(loaded.cases) == 1
    assert loaded.cases[0].id == "a"
    assert loaded.cases[0].risk_tags == ["r"]


def test_load_missing_returns_empty(tmp_path):
    ds = load_dataset(str(tmp_path / "none.json"))
    assert ds.cases == []


def test_by_scenario(tmp_path):
    ds = EvalDataset(name="d", version="1", cases=[
        EvalCase(id="a", question="q", scenario="rag"),
        EvalCase(id="b", question="q", scenario="sql"),
    ])
    assert len(ds.by_scenario("rag")) == 1
    assert len(ds.by_scenario("sql")) == 1
