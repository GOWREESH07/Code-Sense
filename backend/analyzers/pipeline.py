import os
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
from backend.analyzers.base import AnalyzerPlugin, Finding
from backend.analyzers.plugins.radon_plugin import RadonPlugin
from backend.analyzers.plugins.pylint_plugin import PylintPlugin
from backend.analyzers.plugins.bandit_plugin import BanditPlugin
from backend.analyzers.plugins.eslint_plugin import ESLintPlugin
from backend.analyzers.plugins.ck_metrics import ASTMetricsPlugin
from backend.analyzers.plugins.ai_detection_plugin import AIDetectionPlugin


IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__", 
    ".next", "dist", "build", ".pytest_cache", ".ruff_cache", "coverage", ".idea", ".vscode"
}

CODE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


class AnalyzerPipeline:
    def __init__(self):
        self.plugins: List[AnalyzerPlugin] = [
            RadonPlugin(),
            PylintPlugin(),
            BanditPlugin(),
            ESLintPlugin(),
            ASTMetricsPlugin(),
            AIDetectionPlugin(),
        ]


    def discover_files(self, repo_dir: Path) -> List[Tuple[Path, str]]:
        found_files = []
        for root, dirs, files in os.walk(repo_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in CODE_EXTENSIONS:
                    full_path = Path(root) / file
                    lang = CODE_EXTENSIONS[ext]
                    found_files.append((full_path, lang))
        return found_files

    def analyze_repo(self, repo_dir: Path) -> Tuple[List[Dict[str, Any]], List[Finding], Dict[str, Any]]:
        files = self.discover_files(repo_dir)
        per_file_metrics: List[Dict[str, Any]] = []
        all_findings: List[Finding] = []

        total_source_loc = 0
        test_loc = 0
        test_files_count = 0

        for full_path, lang in files:
            rel_path = str(full_path.relative_to(repo_dir))
            is_test_file = (
                "test" in rel_path.lower() 
                or rel_path.startswith("tests/") 
                or rel_path.startswith("__tests__/")
                or full_path.name.startswith("test_")
                or full_path.name.endswith("_test.py")
                or ".test." in full_path.name
                or ".spec." in full_path.name
            )

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            file_metric = {
                "file_path": rel_path,
                "language": lang,
                "loc": len(content.splitlines()),
                "cyclomatic_complexity": 1.0,
                "maintainability_index": 80.0,
                "duplication_pct": 0.0,
                "cbo": 0,
                "lcom": 0,
                "dit": 0,
                "noc": 0,
                "comment_density": 0.0,
                "smells_count": 0,
                "security_vulnerabilities": 0,
                "halstead_volume": 0.0,
                "halstead_difficulty": 0.0,
                "halstead_effort": 0.0,
                "ai_generated_score": 0.0,
                "ai_confidence": "low",
            }

            if is_test_file:
                test_files_count += 1
                test_loc += file_metric["loc"]
            else:
                total_source_loc += file_metric["loc"]

            for plugin in self.plugins:
                if lang in plugin.supported_languages:
                    try:
                        res = plugin.analyze(full_path, content)
                        # Merge metrics
                        for k, v in res.metrics.items():
                            if k in file_metric and isinstance(v, (int, float)):
                                if k == "loc":
                                    file_metric[k] = max(file_metric[k], v)
                                elif k in ["code_smells", "smells_count"]:
                                    file_metric["smells_count"] += v
                                else:
                                    file_metric[k] = v
                            else:
                                file_metric[k] = v

                        # Relativize finding paths
                        for f in res.findings:
                            f.file_path = rel_path
                            all_findings.append(f)
                    except Exception as e:
                        print(f"Error in {plugin.name} on {rel_path}: {e}")

            per_file_metrics.append(file_metric)

        # Estimate test coverage percentage
        if total_source_loc > 0:
            if test_files_count > 0:
                # Based on ratio of test code to source code (standard target is ~0.5 to 1.0)
                coverage_est = min(100.0, round((test_loc / (total_source_loc * 0.6)) * 100.0, 1))
            else:
                coverage_est = 0.0
        else:
            coverage_est = 0.0

        repo_summary = {
            "total_files": len(files),
            "test_files_count": test_files_count,
            "estimated_test_coverage": coverage_est,
        }

        return per_file_metrics, all_findings, repo_summary


pipeline = AnalyzerPipeline()
