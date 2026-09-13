import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ml_model" in data


def test_project_crud():
    # Create project
    create_res = client.post("/api/projects", json={
        "name": "E2E Test Project",
        "description": "Integration test project",
        "repo_url": "https://github.com/example/repo"
    })
    assert create_res.status_code == 200
    proj = create_res.json()
    proj_id = proj["id"]
    assert proj["name"] == "E2E Test Project"

    # List projects
    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    projects = list_res.json()
    assert any(p["id"] == proj_id for p in projects)

    # Get project details
    get_res = client.get(f"/api/projects/{proj_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["project"]["id"] == proj_id

    # Delete project
    del_res = client.delete(f"/api/projects/{proj_id}")
    assert del_res.status_code == 200


def test_predict_endpoint():
    res = client.post("/api/predict", json={
        "loc": 85,
        "cyclomatic_complexity": 7.5,
        "maintainability_index": 65.0,
        "cbo": 4,
        "lcom": 20,
        "duplication_pct": 2.0,
        "dit": 1,
        "noc": 0,
        "comment_density": 18.0
    })
    assert res.status_code == 200
    data = res.json()
    assert "bug_probability" in data
    assert 0.0 <= data["bug_probability"] <= 1.0
    assert "top_contributing_factors" in data
import io
import zipfile
import time


def test_full_analysis_workflow():
    # 1. Create a Project
    p_res = client.post("/api/projects", json={"name": "Pipeline E2E Project"})
    assert p_res.status_code == 200
    proj_id = p_res.json()["id"]

    # 2. Create an in-memory ZIP archive containing sample Python code
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("app/main.py", """
# Main application
import os

def process_data(items):
    total = 0
    for x in items:
        if x > 10:
            total += x * 2
        elif x > 5:
            total += x
        else:
            total -= 1
    return total

class ItemManager:
    def __init__(self):
        self.items = []
    def add(self, item):
        self.items.append(item)
""")
        zf.writestr("app/utils.py", """
# Utility functions
def helper(x):
    return x * 10
""")
        zf.writestr("tests/test_main.py", """
# Test file
def test_dummy():
    assert True
""")
    zip_buf.seek(0)

    # 3. Trigger Analysis via POST /api/projects/{id}/analyze
    files = {"file": ("test_repo.zip", zip_buf.read(), "application/zip")}
    analyze_res = client.post(f"/api/projects/{proj_id}/analyze", files=files)
    assert analyze_res.status_code == 200
    run_id = analyze_res.json()["run_id"]

    # Wait for background task to complete (sync in TestClient with BackgroundTasks)
    status_res = client.get(f"/api/runs/{run_id}/status")
    assert status_res.status_code == 200
    status = status_res.json()["status"]
    assert status == "done"

    # 4. Fetch Results
    results_res = client.get(f"/api/runs/{run_id}")
    assert results_res.status_code == 200
    res_data = results_res.json()
    assert res_data["run"]["overall_score"] is not None
    assert len(res_data["file_metrics"]) >= 2
    assert "recommendations" in res_data
    assert len(res_data["recommendations"]) > 0

    # 5. Test Comparison API
    # Create second run
    zip_buf.seek(0)
    files2 = {"file": ("test_repo2.zip", zip_buf.read(), "application/zip")}
    analyze_res2 = client.post(f"/api/projects/{proj_id}/analyze", files=files2)
    run_id2 = analyze_res2.json()["run_id"]

    compare_res = client.get(f"/api/projects/{proj_id}/compare?run1={run_id}&run2={run_id2}")
    assert compare_res.status_code == 200
    compare_data = compare_res.json()
    assert len(compare_data["metric_diffs"]) == 16
