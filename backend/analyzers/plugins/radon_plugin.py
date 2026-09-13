from pathlib import Path
from typing import List
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit
from radon.raw import analyze as raw_analyze
from backend.analyzers.base import AnalyzerPlugin, PluginResult, Finding


class RadonPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "radon"

    @property
    def supported_languages(self) -> List[str]:
        return ["python"]

    def analyze(self, file_path: Path, content: str) -> PluginResult:
        findings: List[Finding] = []
        metrics = {
            "loc": 0,
            "sloc": 0,
            "comments": 0,
            "blank": 0,
            "cyclomatic_complexity": 1.0,
            "maintainability_index": 100.0,
            "halstead_volume": 0.0,
            "halstead_difficulty": 0.0,
            "halstead_effort": 0.0,
        }

        if not content.strip():
            return PluginResult(metrics=metrics, findings=findings)

        try:
            raw = raw_analyze(content)
            metrics["loc"] = raw.loc
            metrics["sloc"] = raw.sloc
            metrics["comments"] = raw.comments + raw.multi
            metrics["blank"] = raw.blank
        except Exception:
            # Fallback simple line count
            lines = content.splitlines()
            metrics["loc"] = len(lines)
            metrics["sloc"] = len([l for l in lines if l.strip() and not l.strip().startswith("#")])

        try:
            blocks = cc_visit(content)
            if blocks:
                complexities = [b.complexity for b in blocks]
                avg_cc = sum(complexities) / len(complexities)
                metrics["cyclomatic_complexity"] = round(avg_cc, 2)

                for b in blocks:
                    if b.complexity > 15:
                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=b.lineno,
                            rule_id="HIGH_CYCLOMATIC_COMPLEXITY",
                            severity="error",
                            tool="radon",
                            description=f"Function/Class '{b.name}' has excessive cyclomatic complexity ({b.complexity}). Consider refactoring."
                        ))
                    elif b.complexity > 10:
                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=b.lineno,
                            rule_id="MODERATE_CYCLOMATIC_COMPLEXITY",
                            severity="warning",
                            tool="radon",
                            description=f"Function/Class '{b.name}' has cyclomatic complexity ({b.complexity}) exceeding standard threshold (10)."
                        ))
            else:
                metrics["cyclomatic_complexity"] = 1.0
        except Exception:
            metrics["cyclomatic_complexity"] = 1.0

        try:
            mi = mi_visit(content, multi=True)
            metrics["maintainability_index"] = round(max(0.0, min(100.0, mi)), 2)
            if mi < 50.0:
                findings.append(Finding(
                    file_path=str(file_path),
                    line_number=1,
                    rule_id="LOW_MAINTAINABILITY",
                    severity="error",
                    tool="radon",
                    description=f"File has poor maintainability index ({metrics['maintainability_index']:.1f}/100)."
                ))
            elif mi < 65.0:
                findings.append(Finding(
                    file_path=str(file_path),
                    line_number=1,
                    rule_id="MODERATE_MAINTAINABILITY",
                    severity="warning",
                    tool="radon",
                    description=f"File maintainability index is moderate ({metrics['maintainability_index']:.1f}/100)."
                ))
        except Exception:
            metrics["maintainability_index"] = 75.0

        try:
            h_metrics = h_visit(content)
            metrics["halstead_volume"] = round(h_metrics.total.volume, 2)
            metrics["halstead_difficulty"] = round(h_metrics.total.difficulty, 2)
            metrics["halstead_effort"] = round(h_metrics.total.effort, 2)
        except Exception:
            pass

        return PluginResult(metrics=metrics, findings=findings)
