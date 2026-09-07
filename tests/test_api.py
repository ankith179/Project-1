import pytest
from fastapi.testclient import TestClient
from backend.app import app
from database.connection import init_db

client = TestClient(app)


def test_api_health():
    init_db()
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"


def test_api_evaluation_latest():
    response = client.get("/api/evaluation/latest")
    assert response.status_code == 200
    data = response.json()
    assert "requirement_to_code" in data or data.get("status") == "NO_EXPERIMENTS_FOUND"


def test_api_artifacts_and_repositories():
    # Trigger ingestion of benchmark
    ingest_res = client.post("/api/ingest", json={
        "repo_name": "APITestRepo",
        "repo_path": "datasets/benchmark_banking"
    })
    assert ingest_res.status_code == 200
    repo_id = ingest_res.json()["repository_id"]

    # Test repository summary
    summary_res = client.get(f"/api/ingest/repositories/{repo_id}/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["name"] == "APITestRepo"
    assert summary["requirements_count"] == 10
    assert summary["code_artifacts_count"] >= 15
    assert summary["tests_count"] >= 10

    # Test requirements endpoint
    req_res = client.get(f"/api/artifacts/requirements?repo_id={repo_id}")
    assert req_res.status_code == 200
    reqs = req_res.json()
    assert len(reqs) == 10

    # Test single requirement
    single_res = client.get("/api/artifacts/requirements/REQ-001")
    assert single_res.status_code == 200
    assert single_res.json()["req_identifier"] == "REQ-001"

    # Test code artifacts endpoint
    code_res = client.get(f"/api/artifacts/code?repo_id={repo_id}")
    assert code_res.status_code == 200
    assert len(code_res.json()) >= 15

    # Test test artifacts endpoint
    test_res = client.get(f"/api/artifacts/tests?repo_id={repo_id}")
    assert test_res.status_code == 200
    assert len(test_res.json()) >= 10

