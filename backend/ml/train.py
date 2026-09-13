import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import shap

from backend.ml.dataset import load_dataset, FEATURE_NAMES

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_SAVE_PATH = MODEL_DIR / "defect_model.joblib"


def train_defect_models():
    print("==================================================")
    print("CodeSense: Training Defect Prediction Models")
    print("==================================================")

    X, y = load_dataset()
    print(f"Loaded dataset: {len(X)} samples, {len(FEATURE_NAMES)} features.")
    print(f"Defect class balance: {y.value_counts().to_dict()}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = ["f1", "roc_auc", "precision", "recall"]

    # Candidate 1: Random Forest
    rf_model = RandomForestClassifier(n_estimators=120, max_depth=8, min_samples_split=4, random_state=42)
    rf_cv = cross_validate(rf_model, X, y, cv=cv, scoring=scoring)

    # Candidate 2: XGBoost
    xgb_model = XGBClassifier(n_estimators=120, max_depth=5, learning_rate=0.08, eval_metric="logloss", random_state=42)
    xgb_cv = cross_validate(xgb_model, X, y, cv=cv, scoring=scoring)

    # Candidate 3: Support Vector Machine (with Standard Scaling)
    svm_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(probability=True, kernel="rbf", C=1.0, random_state=42))
    ])
    svm_cv = cross_validate(svm_pipeline, X, y, cv=cv, scoring=scoring)

    results = {
        "Random Forest": {
            "model": rf_model,
            "f1": float(np.mean(rf_cv["test_f1"])),
            "roc_auc": float(np.mean(rf_cv["test_roc_auc"])),
            "precision": float(np.mean(rf_cv["test_precision"])),
            "recall": float(np.mean(rf_cv["test_recall"])),
            "is_tree": True,
        },
        "XGBoost": {
            "model": xgb_model,
            "f1": float(np.mean(xgb_cv["test_f1"])),
            "roc_auc": float(np.mean(xgb_cv["test_roc_auc"])),
            "precision": float(np.mean(xgb_cv["test_precision"])),
            "recall": float(np.mean(xgb_cv["test_recall"])),
            "is_tree": True,
        },
        "SVM": {
            "model": svm_pipeline,
            "f1": float(np.mean(svm_cv["test_f1"])),
            "roc_auc": float(np.mean(svm_cv["test_roc_auc"])),
            "precision": float(np.mean(svm_cv["test_precision"])),
            "recall": float(np.mean(svm_cv["test_recall"])),
            "is_tree": False,
        },
    }

    print("\n--- Cross-Validation Model Comparison (5-Fold) ---")
    best_name = None
    best_score = -1.0

    for name, r in results.items():
        composite_score = (r["f1"] + r["roc_auc"]) / 2.0
        print(f"{name:15} -> F1: {r['f1']:.4f} | ROC-AUC: {r['roc_auc']:.4f} | Precision: {r['precision']:.4f} | Recall: {r['recall']:.4f} (Composite: {composite_score:.4f})")
        if composite_score > best_score:
            best_score = composite_score
            best_name = name

    print(f"\nWinner: {best_name} selected based on cross-validated F1/AUC ({best_score:.4f})")

    best_candidate = results[best_name]
    final_model = best_candidate["model"]
    final_model.fit(X, y)

    # Prepare SHAP Explainer
    print("Fitting SHAP Explainer...")
    explainer = None
    try:
        if best_candidate["is_tree"]:
            explainer = shap.TreeExplainer(final_model)
        else:
            background = shap.sample(X, 50, random_state=42)
            explainer = shap.KernelExplainer(final_model.predict_proba, background)
    except Exception as e:
        print(f"SHAP explainer init warning: {e}")

    artifact = {
        "model_name": best_name,
        "model": final_model,
        "feature_names": FEATURE_NAMES,
        "metrics": {
            "f1": best_candidate["f1"],
            "roc_auc": best_candidate["roc_auc"],
            "precision": best_candidate["precision"],
            "recall": best_candidate["recall"],
        },
        "explainer": explainer,
        "is_tree": best_candidate["is_tree"],
    }

    joblib.dump(artifact, MODEL_SAVE_PATH)
    print(f"Model saved successfully to {MODEL_SAVE_PATH}")
    return artifact


if __name__ == "__main__":
    train_defect_models()
