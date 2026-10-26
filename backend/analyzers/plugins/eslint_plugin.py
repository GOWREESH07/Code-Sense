import json
import subprocess
import shutil
import re
from pathlib import Path
from typing import List
from backend.analyzers.base import AnalyzerPlugin, PluginResult, Finding


class ESLintPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "eslint"

    @property
    def supported_languages(self) -> List[str]:
        return ["javascript", "typescript"]

    def analyze(self, file_path: Path, content: str) -> PluginResult:
        findings: List[Finding] = []
        metrics = {
            "loc": len(content.splitlines()),
            "code_smells": 0,
            "security_vulnerabilities": 0,
            "cyclomatic_complexity": 1.0,
            "maintainability_index": 75.0,
        }

        # Calculate JS/TS basic complexity heuristic (branches: if, else if, for, while, case, catch, &&, ||, ?)
        branch_count = len(re.findall(r'\b(if|for|while|case|catch)\b|\?\s*[^:]+\s*:|&&|\|\|', content))
        func_count = len(re.findall(r'\b(function\b|=>\s*\{)', content)) or 1
        avg_cc = max(1.0, round(1.0 + (branch_count / func_count), 2))
        metrics["cyclomatic_complexity"] = avg_cc

        # Heuristic Maintainability Index for JS/TS
        loc = metrics["loc"]
        if loc > 0:
            mi = max(20.0, min(100.0, 171 - 5.2 * (avg_cc ** 0.5) - 0.23 * loc))
            metrics["maintainability_index"] = round(mi, 2)

        # Attempt to run eslint if directly installed
        eslint_bin = shutil.which("eslint")
        eslint_ran = False
        if eslint_bin and file_path.exists():
            try:
                cmd = [
                    eslint_bin,
                    "--format", "json",
                    "--no-eslintrc",
                    "--rule", "no-eval: error",
                    "--rule", "no-unused-vars: warn",
                    "--rule", "no-console: warn",
                    "--rule", "eqeqeq: warn",
                    str(file_path)
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.stdout.strip():
                    try:
                        reports = json.loads(res.stdout)
                        for rep in reports:
                            for msg in rep.get("messages", []):
                                rule_id = msg.get("ruleId") or "eslint-error"
                                severity_val = msg.get("severity", 1) # 1: warn, 2: error
                                sev = "error" if severity_val == 2 else "warning"
                                is_sec = "eval" in rule_id or "security" in rule_id
                                if is_sec:
                                    metrics["security_vulnerabilities"] += 1
                                else:
                                    metrics["code_smells"] += 1

                                findings.append(Finding(
                                    file_path=str(file_path),
                                    line_number=msg.get("line", 1),
                                    rule_id=rule_id,
                                    severity=sev,
                                    tool="eslint",
                                    description=msg.get("message", "ESLint finding"),
                                ))
                        eslint_ran = True
                    except Exception:
                        pass
            except Exception:
                pass

        # If eslint wasn't runnable or returned empty, run built-in JS/TS lint checks
        if not eslint_ran:
            lines = content.splitlines()
            for idx, line in enumerate(lines, start=1):
                # Check eval
                if re.search(r'\beval\(', line):
                    findings.append(Finding(
                        file_path=str(file_path),
                        line_number=idx,
                        rule_id="no-eval",
                        severity="error",
                        tool="eslint",
                        description="Forbidden use of eval() detected, poses critical code injection risk."
                    ))
                    metrics["security_vulnerabilities"] += 1
                # Check innerHTML
                if re.search(r'\.innerHTML\s*=', line):
                    findings.append(Finding(
                        file_path=str(file_path),
                        line_number=idx,
                        rule_id="no-inner-html",
                        severity="warning",
                        tool="eslint",
                        description="Direct assignment to innerHTML can cause XSS vulnerabilities. Use textContent or sanitized DOM."
                    ))
                    metrics["security_vulnerabilities"] += 1
                # Check loose equality == / !=
                if re.search(r'[^!=<>]==[^=]|[^!<=>]!=[^=]', line):
                    findings.append(Finding(
                        file_path=str(file_path),
                        line_number=idx,
                        rule_id="eqeqeq",
                        severity="info",
                        tool="eslint",
                        description="Expected '===' or '!==' and instead saw loose equality."
                    ))
                    metrics["code_smells"] += 1
                # Check console.log
                if re.search(r'\bconsole\.(log|debug|warn)\(', line):
                    findings.append(Finding(
                        file_path=str(file_path),
                        line_number=idx,
                        rule_id="no-console",
                        severity="info",
                        tool="eslint",
                        description="Unexpected console statement in production code."
                    ))
                    metrics["code_smells"] += 1

        if avg_cc > 15:
            findings.append(Finding(
                file_path=str(file_path),
                line_number=1,
                rule_id="COMPLEX_MODULE",
                severity="warning",
                tool="eslint",
                description=f"JavaScript module has high cyclomatic complexity ({avg_cc})."
            ))

        return PluginResult(metrics=metrics, findings=findings)
