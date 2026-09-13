import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import shutil
import tempfile
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.db.database import db
from backend.services.analysis_runner import run_analysis_pipeline
from backend.ml.predictor import predictor

app = FastAPI(
    title="CodeSense API",
    description="AI-Powered Software Quality Analyser API",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Models
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    repo_url: Optional[str] = ""


class PredictRequest(BaseModel):
    loc: float = 50.0
    cyclomatic_complexity: float = 3.0
    maintainability_index: float = 75.0
    duplication_pct: float = 0.0
    cbo: float = 2.0
    lcom: float = 20.0
    dit: float = 1.0
    noc: float = 0.0
    comment_density: float = 15.0
    halstead_volume: Optional[float] = None
    halstead_difficulty: Optional[float] = None
    halstead_effort: Optional[float] = None


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CodeSense API", "ml_model": predictor.model_name}


# Projects Endpoints
@app.post("/api/projects")
def create_project(req: ProjectCreateRequest):
    proj = db.create_project(
        name=req.name,
        description=req.description or "",
        repo_url=req.repo_url or "",
    )
    return proj


@app.get("/api/projects")
def list_projects():
    return db.list_projects()


@app.get("/api/projects/{project_id}")
def get_project_details(project_id: str):
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    runs = db.list_runs_for_project(project_id)
    return {"project": proj, "runs": runs}


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    success = db.delete_project(project_id)
    return {"success": success}


# Analysis Endpoints
@app.post("/api/projects/{project_id}/analyze")
async def trigger_analysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    github_url: Optional[str] = Form(None),
):
    proj = db.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file and not github_url:
        raise HTTPException(status_code=400, detail="Please provide either a ZIP archive file or a GitHub URL.")

    # Create run record
    run = db.create_run(project_id)
    run_id = run["id"]

    zip_path = None
    if file:
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Uploaded file must be a .zip archive.")
        save_path = UPLOAD_DIR / f"{run_id}_{file.filename}"
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        zip_path = str(save_path)

    # Queue background task
    background_tasks.add_task(
        run_analysis_pipeline,
        run_id=run_id,
        zip_path=zip_path,
        github_url=github_url,
    )

    return {
        "run_id": run_id,
        "project_id": project_id,
        "status": "queued",
        "message": "Analysis started in background.",
    }


@app.get("/api/runs/{run_id}/status")
def get_run_status(run_id: str):
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return {
        "id": run["id"],
        "project_id": run["project_id"],
        "status": run["status"],
        "error_message": run.get("error_message"),
        "created_at": run.get("created_at"),
        "completed_at": run.get("completed_at"),
    }


@app.get("/api/runs/{run_id}")
def get_run_results(run_id: str):
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    file_metrics = db.get_file_metrics(run_id)
    defects = db.get_defects(run_id)
    recommendations = db.get_recommendations(run_id)

    return {
        "run": run,
        "file_metrics": file_metrics,
        "defects": defects,
        "recommendations": recommendations,
    }


@app.get("/api/projects/{project_id}/compare")
def compare_runs(
    project_id: str,
    run1: str = Query(..., description="Base run ID"),
    run2: str = Query(..., description="Comparison run ID"),
):
    r1 = db.get_run(run1)
    r2 = db.get_run(run2)

    if not r1 or not r2:
        raise HTTPException(status_code=404, detail="One or both runs not found")

    s1 = r1.get("summary") or {}
    s2 = r2.get("summary") or {}

    metric_keys = [
        ("overall_quality_score", "Overall Quality Score"),
        ("loc", "Total Lines of Code"),
        ("cyclomatic_complexity", "Average Cyclomatic Complexity"),
        ("maintainability_index", "Maintainability Index"),
        ("duplication_pct", "Code Duplication %"),
        ("cbo", "Coupling Between Objects (CBO)"),
        ("lcom", "Lack of Cohesion (LCOM)"),
        ("dit", "Depth of Inheritance (DIT)"),
        ("noc", "Number of Children (NOC)"),
        ("defect_density", "Defect Density (per KLOC)"),
        ("code_smells", "Code Smells Count"),
        ("tech_debt_minutes", "Technical Debt (minutes)"),
        ("test_coverage_pct", "Test Coverage %"),
        ("comment_density", "Comment Density %"),
        ("security_vulnerabilities", "Security Vulnerabilities"),
        ("bug_prediction_score", "Bug Prediction Score"),
    ]

    diffs = []
    for key, label in metric_keys:
        val1 = s1.get(key, 0)
        val2 = s2.get(key, 0)
        delta = round(val2 - val1, 2)
        diffs.append({
            "metric": key,
            "label": label,
            "base_value": val1,
            "compare_value": val2,
            "delta": delta,
            "improved": (delta < 0 if key in ["cyclomatic_complexity", "duplication_pct", "cbo", "lcom", "defect_density", "code_smells", "tech_debt_minutes", "security_vulnerabilities", "bug_prediction_score"] else delta > 0),
        })

    return {
        "project_id": project_id,
        "run1": {"id": r1["id"], "created_at": r1.get("created_at"), "overall_score": r1.get("overall_score")},
        "run2": {"id": r2["id"], "created_at": r2.get("created_at"), "overall_score": r2.get("overall_score")},
        "metric_diffs": diffs,
    }


# Standalone ML Predict Endpoint
@app.post("/api/predict")
def predict_defect(req: PredictRequest):
    res = predictor.predict_file(req.dict())
    return res
