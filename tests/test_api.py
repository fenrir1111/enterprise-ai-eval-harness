import pytest
from fastapi.testclient import TestClient

from ai_eval_harness.main import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "rag-v1" in data["services"]


def test_dataset_overview(client):
    r = client.get("/dataset")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert "rag" in data["by_scenario"]


def test_evaluate(client):
    r = client.post("/evaluate", json={"service": "rag-v1"})
    assert r.status_code == 200
    data = r.json()
    assert "metrics" in data
    assert "report_md" in data
    assert data["metrics"]["total"] > 0


def test_evaluate_unknown_service(client):
    r = client.post("/evaluate", json={"service": "nope"})
    assert r.status_code == 200
    assert "error" in r.json()


def test_evaluate_scenario_filter(client):
    r = client.post("/evaluate", json={"service": "rag-v1", "scenarios": ["rag"]})
    data = r.json()
    # 仅 rag 场景（样例集中 4 条）
    assert data["metrics"]["total"] == 4


def test_compare(client):
    r = client.post("/compare", json={"base": "rag-v0", "candidate": "rag-v1"})
    assert r.status_code == 200
    data = r.json()
    assert "metric_delta" in data
    assert data["improved_count"] >= 1


def test_export_markdown(client, tmp_path):
    r = client.post("/export", json={"service": "rag-v1", "format": "markdown"})
    assert r.status_code == 200
    data = r.json()
    assert data["format"] == "markdown"
    assert data["path"].endswith(".md")
