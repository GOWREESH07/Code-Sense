import json
import subprocess
import sys
from pathlib import Path
from typing import List
from backend.analyzers.base import AnalyzerPlugin, PluginResult, Finding


class PylintPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "pylint"

    @property
    def supported_languages(self) -> List[str]:
        return ["python"]

    def analyze(self, file_path: Path, content: str) -> PluginResult:
        findings: List[Finding] = []
        metrics = {"code_smells": 0, "conventions": 0, "refactors": 0, "warnings": 0, "errors": 0}

        # We can run pylint CLI on the file path directly
        if not file_path.exists():
            return PluginResult(metrics=metrics, findings=findings)

        try:
            cmd = [
                sys.executable, "-m", "pylint",
                str(file_path),
                "--output-format=json",
                "--score=no",
                "--disable=C0114,C0115,C0116", # Don't flood with missing module/class/func docstring for every tiny item
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = res.stdout.strip()

            if output:
                try:
                    data = json.loads(output)
                    for item in data:
                        category = item.get("type", "warning") # convention, refactor, warning, error, fatal
                        rule_id = item.get("symbol") or item.get("message-id", "PYLINT")
                        msg = item.get("message", "")
                        line = item.get("line", 1)

                        if category in ["fatal", "error"]:
                            sev = "error"
                            metrics["errors"] += 1
                        elif category in ["warning"]:
                            sev = "warning"
                            metrics["warnings"] += 1
                        elif category in ["refactor"]:
                            sev = "warning"
                            metrics["refactors"] += 1
                        else:
                            sev = "info"
                            metrics["conventions"] += 1

                        findings.append(Finding(
                            file_path=str(file_path),
                            line_number=line,
                            rule_id=rule_id,
                            severity=sev,
                            tool="pylint",
                            description=msg,
                        ))
                    metrics["code_smells"] = len(findings)
                except Exception:
                    pass
        except Exception as e:
            # Non-fatal if pylint encounters syntax error or timeout
            pass

        return PluginResult(metrics=metrics, findings=findings)
