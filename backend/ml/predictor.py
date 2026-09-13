import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
import shap

from backend.ml.dataset import FEATURE_NAMES

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "defect_model.joblib"


class DefectPredictor:
    def __init__(self):
        self.artifact = None
        self._load_or_train()

    def _load_or_train(self):
        if MODEL_PATH.exists():
            try:
                self.artifact = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"[Predictor] Error loading model ({e}), retraining...")
                self._train()
        else:
            self._train()

    def _train(self):
        from backend.ml.train import train_defect_models
        self.artifact = train_defect_models()

    @property
    def model(self):
        return self.artifact["model"]

    @property
    def explainer(self):
        return self.artifact.get("explainer")

    @property
    def model_name(self):
        return self.artifact.get("model_name", "Defect Classifier")

    def predict_file(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Predict bug probability and generate plain-language risk explanation."""
        def safe_float(val, default):
            if val is None:
                return float(default)
            try:
                return float(val)
            except Exception:
                return float(default)

        loc = safe_float(metrics.get("loc"), 10.0)
        cc = safe_float(metrics.get("cyclomatic_complexity"), 1.0)
        h_vol = safe_float(metrics.get("halstead_volume"), loc * 25.0)
        h_diff = safe_float(metrics.get("halstead_difficulty"), cc * 1.8)
        h_eff = safe_float(metrics.get("halstead_effort"), h_vol * h_diff)

        feature_values = {
            "loc": loc,
            "cyclomatic_complexity": cc,
            "maintainability_index": safe_float(metrics.get("maintainability_index"), 75.0),
            "duplication_pct": safe_float(metrics.get("duplication_pct"), 0.0),
            "cbo": safe_float(metrics.get("cbo"), 0.0),
            "lcom": safe_float(metrics.get("lcom"), 0.0),
            "dit": safe_float(metrics.get("dit"), 0.0),
            "noc": safe_float(metrics.get("noc"), 0.0),
            "comment_density": safe_float(metrics.get("comment_density"), 15.0),
            "halstead_volume": h_vol,
            "halstead_difficulty": h_diff,
            "halstead_effort": h_eff,
        }

        row_df = pd.DataFrame([[feature_values[f] for f in FEATURE_NAMES]], columns=FEATURE_NAMES)

        try:
            proba = float(self.model.predict_proba(row_df)[0][1])
        except Exception:
            proba = min(0.99, max(0.01, (cc / 30.0) * 0.5 + (100 - feature_values["maintainability_index"]) / 200.0))

        risk_level = "Low"
        if proba >= 0.70:
            risk_level = "Critical"
        elif proba >= 0.45:
            risk_level = "High"
        elif proba >= 0.25:
            risk_level = "Medium"

        contributions = self._explain(row_df, feature_values)

        return {
            "bug_probability": round(proba, 3),
            "risk_level": risk_level,
            "model_used": self.model_name,
            "top_contributing_factors": contributions,
        }

    def _explain(self, row_df: pd.DataFrame, feature_values: Dict[str, float]) -> List[Dict[str, Any]]:
        contributions = []
        friendly_names = {
            "cyclomatic_complexity": "Cyclomatic Complexity",
            "maintainability_index": "Maintainability Index",
            "loc": "Lines of Code (LOC)",
            "cbo": "Coupling Between Objects (CBO)",
            "lcom": "Lack of Cohesion (LCOM)",
            "duplication_pct": "Code Duplication",
            "halstead_effort": "Halstead Cognitive Effort",
            "comment_density": "Comment Density",
            "dit": "Depth of Inheritance",
            "noc": "Number of Children",
        }

        try:
            if self.explainer:
                shap_vals = self.explainer.shap_values(row_df)
                if isinstance(shap_vals, list) and len(shap_vals) > 1:
                    vals = shap_vals[1][0]
                elif hasattr(shap_vals, "values"):
                    vals = shap_vals.values[0]
                    if vals.ndim > 1:
                        vals = vals[:, 1]
                else:
                    vals = shap_vals[0]

                for feat_name, shap_val in zip(FEATURE_NAMES, vals):
                    val = feature_values.get(feat_name, 0.0)
                    impact = float(shap_val)
                    if impact > 0.01:
                        readable = friendly_names.get(feat_name, feat_name.replace("_", " ").title())
                        explanation = f"{readable} ({val:g}) increases defect likelihood (+{impact*100:.1f}%)"
                        contributions.append({
                            "feature": feat_name,
                            "display_name": readable,
                            "value": val,
                            "shap_value": round(impact, 4),
                            "impact_pct": round(impact * 100, 1),
                            "explanation": explanation
                        })

                contributions.sort(key=lambda x: x["shap_value"], reverse=True)
        except Exception:
            cc = feature_values["cyclomatic_complexity"]
            if cc > 10:
                contributions.append({
                    "feature": "cyclomatic_complexity",
                    "display_name": "Cyclomatic Complexity",
                    "value": cc,
                    "shap_value": 0.25,
                    "impact_pct": 25.0,
                    "explanation": f"High cyclomatic complexity ({cc}) increases branch error probability."
                })
            mi = feature_values["maintainability_index"]
            if mi < 60:
                contributions.append({
                    "feature": "maintainability_index",
                    "display_name": "Maintainability Index",
                    "value": mi,
                    "shap_value": 0.20,
                    "impact_pct": 20.0,
                    "explanation": f"Low maintainability score ({mi}/100) indicates high modification difficulty."
                })

        return contributions[:4]


predictor = DefectPredictor()
