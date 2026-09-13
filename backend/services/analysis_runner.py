import os
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

from backend.db.database import db
from backend.analyzers.pipeline import pipeline
from backend.services.metrics_service import metrics_service
from backend.ml.predictor import predictor
from backend.recommendations.factory import get_recommendation_provider


def run_analysis_pipeline(run_id: str, zip_path: Optional[str] = None, github_url: Optional[str] = None):
    temp_dir = tempfile.mkdtemp(prefix=f"codesense_{run_id}_")
    work_dir = Path(temp_dir)

    try:
        db.update_run_status(run_id, "analyzing")

        # 1. Ingest Repository
        target_dir = work_dir / "repo"
        target_dir.mkdir(parents=True, exist_ok=True)

        if zip_path and os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(target_dir)
            # If zipped archive has a single top-level root folder, use that
            subdirs = [p for p in target_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
            if len(subdirs) == 1 and not any(p.is_file() for p in target_dir.iterdir()):
                target_dir = subdirs[0]

        elif github_url:
            print(f"[Runner] Cloning {github_url} into {target_dir}...")
            # Shallow clone
            cmd = ["git", "clone", "--depth", "1", github_url, str(target_dir)]
            subprocess.run(cmd, check=True, capture_output=True, timeout=90)

        else:
            raise ValueError("No archive file or GitHub URL provided.")

        # 2. Run Static Analysis Pipeline
        file_metrics, findings, repo_summary = pipeline.analyze_repo(target_dir)
        if not file_metrics:
            raise ValueError("No supported source code files found (.py, .js, .ts).")

        # 3. ML Defect Prediction
        db.update_run_status(run_id, "scoring")
        for m in file_metrics:
            pred = predictor.predict_file(m)
            m["bug_probability"] = pred["bug_probability"]
            m["risk_level"] = pred["risk_level"]
            m["top_contributing_factors"] = pred["top_contributing_factors"]

        # Sort files by highest risk
        file_metrics.sort(key=lambda x: (x.get("bug_probability", 0), x.get("cyclomatic_complexity", 0)), reverse=True)

        # 4. Metric Aggregation
        agg_metrics = metrics_service.aggregate_metrics(file_metrics, findings, repo_summary)

        # 5. AI Recommendations
        db.update_run_status(run_id, "recommending")
        provider = get_recommendation_provider()
        recs = provider.generate_recommendations(
            metrics_summary=agg_metrics,
            top_risky_files=file_metrics[:5],
            findings=findings,
        )

        # 6. Save to Database
        db.save_file_metrics(run_id, file_metrics)

        defects_payload = [
            {
                "file_path": f.file_path,
                "line_number": f.line_number,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "tool": f.tool,
                "description": f.description,
            }
            for f in findings
        ]
        db.save_defects(run_id, defects_payload)

        recs_payload = [r.dict() for r in recs]
        db.save_recommendations(run_id, recs_payload)

        # Update run summary
        summary = {
            **agg_metrics,
            "top_risky_files": [
                {
                    "file_path": f["file_path"],
                    "loc": f["loc"],
                    "cyclomatic_complexity": f["cyclomatic_complexity"],
                    "maintainability_index": f["maintainability_index"],
                    "cbo": f.get("cbo", 0),
                    "bug_probability": f["bug_probability"],
                    "risk_level": f["risk_level"],
                    "top_contributing_factors": f["top_contributing_factors"],
                }
                for f in file_metrics[:5]
            ],
            "total_files": len(file_metrics),
            "findings_count": len(findings),
        }

        db.update_run_results(
            run_id=run_id,
            overall_score=agg_metrics["overall_quality_score"],
            total_loc=agg_metrics["loc"],
            total_complexity=agg_metrics["cyclomatic_complexity"],
            bug_probability=agg_metrics["bug_prediction_score"],
            tech_debt_minutes=agg_metrics["tech_debt_minutes"],
            summary=summary,
        )
        print(f"[Runner] Analysis run {run_id} completed successfully.")

    except Exception as e:
        print(f"[Runner] Analysis run {run_id} failed: {e}")
        db.update_run_status(run_id, "failed", str(e))

    finally:
        # Clean up temporary directories
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass
