import pytest
from pathlib import Path
from backend.analyzers.plugins.radon_plugin import RadonPlugin
from backend.analyzers.plugins.ck_metrics import ASTMetricsPlugin
from backend.services.metrics_service import MetricsService


SAMPLE_PYTHON_CODE = """
# This is a sample calculation module
# Contains comments and class structure

class BaseCalculator:
    def __init__(self):
        self.history = []

class ScientificCalculator(BaseCalculator):
    def __init__(self):
        super().__init__()
        self.memory = 0

    def complex_operation(self, a, b, op):
        # A method with branching
        if op == "add":
            res = a + b
        elif op == "sub":
            res = a - b
        elif op == "mul":
            res = a * b
        elif op == "div":
            if b != 0:
                res = a / b
            else:
                res = 0
        else:
            res = 0
        self.memory = res
        self.history.append(res)
        return res

    def get_memory(self):
        return self.memory
"""


def test_radon_plugin(tmp_path):
    plugin = RadonPlugin()
    test_file = tmp_path / "calc.py"
    test_file.write_text(SAMPLE_PYTHON_CODE)

    res = plugin.analyze(test_file, SAMPLE_PYTHON_CODE)
    assert res.metrics["loc"] > 20
    assert res.metrics["cyclomatic_complexity"] >= 2.0
    assert 0 <= res.metrics["maintainability_index"] <= 100
    assert res.metrics["comments"] > 0


def test_ck_metrics_plugin(tmp_path):
    plugin = ASTMetricsPlugin()
    test_file = tmp_path / "calc.py"
    test_file.write_text(SAMPLE_PYTHON_CODE)

    res = plugin.analyze(test_file, SAMPLE_PYTHON_CODE)
    assert res.metrics["dit"] >= 1  # Inherits from BaseCalculator
    assert res.metrics["comment_density"] > 0.0
    assert "cbo" in res.metrics
    assert "lcom" in res.metrics


def test_technical_debt_calculation():
    file_metrics = [
        {"cyclomatic_complexity": 18.0, "maintainability_index": 45.0, "duplication_pct": 12.0}
    ]
    findings = []
    debt = MetricsService.calculate_technical_debt(file_metrics, findings)
    assert debt > 0
