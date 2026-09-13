import pytest
from backend.ml.predictor import predictor


def test_defect_predictor_valid_output():
    metrics = {
        "loc": 120,
        "cyclomatic_complexity": 14.0,
        "maintainability_index": 52.0,
        "cbo": 8,
        "lcom": 40,
        "duplication_pct": 5.0,
        "comment_density": 10.0,
    }
    result = predictor.predict_file(metrics)

    assert "bug_probability" in result
    assert 0.0 <= result["bug_probability"] <= 1.0
    assert result["risk_level"] in ["Low", "Medium", "High", "Critical"]
    assert "top_contributing_factors" in result
    assert isinstance(result["top_contributing_factors"], list)

    for factor in result["top_contributing_factors"]:
        assert "feature" in factor
        assert "explanation" in factor
