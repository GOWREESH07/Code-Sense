import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ml.ai_features import AIFeatureExtractor
from backend.ml.ai_detector import ai_detector, AICodeDetector
from backend.analyzers.pipeline import AnalyzerPipeline

client = TestClient(app)

SAMPLE_AI_CODE = '''def fetch_user_data_by_id(user_id: int) -> dict:
    """
    Fetch user data from the database by user ID.

    Parameters:
        user_id (int): The unique identifier of the user.

    Returns:
        dict: A dictionary containing the user details.

    Raises:
        ValueError: If user_id is non-positive.
    """
    if user_id <= 0:
        raise ValueError("Invalid user ID provided. Must be positive.")

    result = {}
    temp_data = None
    data_list = []

    try:
        connection = None
        data_list.append({"id": user_id, "active": True})
        result["user"] = data_list[0]
    except Exception as error:
        raise RuntimeError(f"Database error: {error}")

    return result
'''

SAMPLE_HUMAN_CODE = '''import os, sys

def do_stuff(x):
    # quick hack for now
    if not x: return None
    res = []
    for i in x:
        if i % 2:
            res.append(i * 3) # weird logic
        else:
            continue
    return res

class Foo:
    def __init__(self):
        self._val = 42
'''

def test_feature_extraction_structure():
    features = AIFeatureExtractor.extract_features(SAMPLE_AI_CODE, "python")
    assert len(features) == len(AIFeatureExtractor.FEATURE_NAMES)
    for name in AIFeatureExtractor.FEATURE_NAMES:
        assert name in features
        assert isinstance(features[name], (int, float))
        assert features[name] >= 0.0

def test_ai_detector_prediction_output():
    res = ai_detector.predict_file(SAMPLE_AI_CODE, "python")
    assert "ai_generated_score" in res
    assert 0.0 <= res["ai_generated_score"] <= 1.0
    assert res["confidence"] in ["low", "medium", "high"]
    assert res["caveat"] == AICodeDetector.CAVEAT
    assert res["loc"] > 0
    assert "features" in res

def test_short_file_confidence():
    short_code = "def add(a, b):\n    return a + b\n"
    res = ai_detector.predict_file(short_code, "python")
    # Files under 15 lines must have 'low' confidence due to limited sample size
    assert res["confidence"] == "low"
    assert res["loc"] < 15

def test_api_predict_ai_generated():
    # Test POST /api/predict/ai-generated
    resp = client.post("/api/predict/ai-generated", json={"code": SAMPLE_AI_CODE, "language": "python"})
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_generated_score" in data
    assert "confidence" in data
    assert data["caveat"] == AICodeDetector.CAVEAT

    # Test POST /predict/ai-generated (alias) with 'content' parameter
    resp_alias = client.post("/predict/ai-generated", json={"content": SAMPLE_HUMAN_CODE})
    assert resp_alias.status_code == 200
    data_alias = resp_alias.json()
    assert "ai_generated_score" in data_alias
    assert "confidence" in data_alias

def test_pipeline_ai_detection(tmp_path):
    from pathlib import Path
    from backend.analyzers.plugins.ai_detection_plugin import AIDetectionPlugin
    plugin = AIDetectionPlugin()
    res = plugin.analyze(Path("test_module.py"), SAMPLE_AI_CODE)
    metrics = res.metrics
    assert "ai_generated_score" in metrics
    assert 0.0 <= metrics["ai_generated_score"] <= 1.0
    assert "ai_confidence" in metrics
    assert metrics["ai_confidence"] in ["low", "medium", "high"]

    # Test full pipeline execution on a directory
    test_file = tmp_path / "sample.py"
    test_file.write_text(SAMPLE_AI_CODE, encoding="utf-8")
    pipeline = AnalyzerPipeline()
    per_file_metrics, findings, summary = pipeline.analyze_repo(tmp_path)
    assert len(per_file_metrics) == 1
    assert "ai_generated_score" in per_file_metrics[0]
    assert "ai_confidence" in per_file_metrics[0]

