from pathlib import Path
from typing import List
from backend.analyzers.base import AnalyzerPlugin, PluginResult, Finding
from backend.ml.ai_detector import ai_detector


class AIDetectionPlugin(AnalyzerPlugin):
    @property
    def name(self) -> str:
        return "ai_detection"

    @property
    def supported_languages(self) -> List[str]:
        return ["python", "javascript", "typescript"]

    def analyze(self, file_path: Path, content: str) -> PluginResult:
        ext = file_path.suffix.lower()
        lang = "python" if ext == ".py" else "javascript"

        res = ai_detector.predict_file(content, language=lang)
        score = res["ai_generated_score"]
        confidence = res["confidence"]
        scaffolding_score = res["features"].get("scaffolding_score", 0.0)

        findings: List[Finding] = []
        if scaffolding_score >= 0.5:
            findings.append(
                Finding(
                    file_path=str(file_path),
                    line_number=1,
                    rule_id="AI_SCAFFOLDING_DETECTED",
                    severity="info",
                    tool="ai_detection",
                    description=(
                        f"Heuristic signals indicate likely AI-generated template scaffolding "
                        f"(estimated assistant probability: {int(score * 100)}%, confidence: {confidence})."
                    ),
                )
            )

        return PluginResult(
            metrics={
                "ai_generated_score": score,
                "ai_confidence": confidence,
            },
            findings=findings,
        )
