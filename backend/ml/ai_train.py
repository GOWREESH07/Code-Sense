import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import joblib
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from backend.ml.ai_dataset import generate_augmented_dataset

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_SAVE_PATH = MODELS_DIR / "ai_code_model.joblib"


def train_ai_detector():
    print("[AI Train] Generating labeled dataset (human vs AI code)...")
    X, y = generate_augmented_dataset()
    print(f"[AI Train] Dataset shape: {X.shape}, Class distribution: {y.value_counts().to_dict()}")

    # Build pipeline with GradientBoostingClassifier
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.08,
            max_depth=3,
            random_state=42
        ))
    ])

    # 5-fold cross validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    roc_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
    f1_scores = cross_val_score(pipeline, X, y, cv=cv, scoring="f1")

    print(f"[AI Train] 5-Fold Cross-Validation:")
    print(f"  ROC-AUC: {roc_scores.mean():.4f} (+/- {roc_scores.std():.4f})")
    print(f"  F1 Score: {f1_scores.mean():.4f} (+/- {f1_scores.std():.4f})")

    # Fit full model
    pipeline.fit(X, y)

    # Save artifact
    artifact = {
        "model": pipeline,
        "feature_names": list(X.columns),
        "metrics": {
            "roc_auc": float(roc_scores.mean()),
            "f1": float(f1_scores.mean()),
        },
        "model_name": "GradientBoosting (AI Code Detector)",
    }
    joblib.dump(artifact, MODEL_SAVE_PATH)
    print(f"[AI Train] Model successfully saved to {MODEL_SAVE_PATH}")
    return artifact


if __name__ == "__main__":
    train_ai_detector()
