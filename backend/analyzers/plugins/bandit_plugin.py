import json
import subprocess
import sys
from pathlib import Path
from typing import List
from backend.analyzers.base import AnalyzerPlugin, PluginResult, Finding


class BanditPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "bandit"

    @property
    def supported_languages(self) -> List[str]:
        return ["python"]

    def analyze(self, file_path: Path, content: str) -> PluginResult:
        findings: List[Finding] = []
        metrics = {"security_vulnerabilities": 0, "high_severity": 0, "medium_severity": 0, "low_severity": 0}

        if not file_path.exists():
            return PluginResult(metrics=metrics, findings=findings)

        try:
            cmd = [
                sys.executable, "-m", "bandit",
                "-f", "json",
                "-q",
                str(file_path),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = res.stdout.strip()

            if output:
                try:
                    data = json.loads(output)
                    results = data.get("results", [])
                    for issue in results:
                        issue_sev = issue.get("issue_severity", "LOW").upper()
                        if issue_sev == "HIGH":
                            sev = "critical"
                            metrics["high_severity"] += 1
                        elif issue_sev == "MEDIUM":
                            sev = "error"
                            metrics["medium_severity"] += 1
                        else:
                            sev = "warning"
                            metrics["low_severity"] += 1

                        test_id = issue.get("test_id", "B000")
                        rule_name = issue.get("test_name", "SECURITY_ISSUE")
                        msg = issue.get("issue_text", "Security vulnerability detected")
                        line = issue.get("line_number", 1)

                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=line,
                            rule_id=f"{test_id}_{rule_name}",
                            severity=sev,
                            tool="bandit",
                            description=msg,
                        ))
                    metrics["security_vulnerabilities"] = len(findings)
                except Exception:
                    pass
        except Exception:
            pass

        return PluginResult(metrics=metrics, findings=findings)
