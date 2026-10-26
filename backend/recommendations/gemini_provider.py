import os
import json
from typing import List, Dict, Any
from backend.recommendations.base import RecommendationProvider, RecommendationItem
from backend.recommendations.rule_provider import RuleBasedRecommendationProvider


class GeminiRecommendationProvider(RecommendationProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.fallback = RuleBasedRecommendationProvider()

    def generate_recommendations(
        self,
        metrics_summary: Dict[str, Any],
        top_risky_files: List[Dict[str, Any]],
        findings: List[Any],
    ) -> List[RecommendationItem]:
        try:
            # Prepare structured context
            context_data = {
                "metrics_summary": metrics_summary,
                "top_risky_files": top_risky_files[:5],
                "sample_findings": [
                    {
                        "file": getattr(f, "file_path", ""),
                        "tool": getattr(f, "tool", ""),
                        "rule": getattr(f, "rule_id", ""),
                        "severity": getattr(f, "severity", ""),
                        "desc": getattr(f, "description", "")[:120],
                    }
                    for f in findings[:15]
                ],
            }

            prompt = f"""
You are an expert Principal Software Architect analyzing a software codebase using the CodeSense static and ML quality pipeline.
Based on the following analysis findings, produce between 3 and 5 prioritized, high-impact recommendations for engineering leadership and developers.

ANALYSIS FINDINGS:
{json.dumps(context_data, indent=2)}

OUTPUT REQUIREMENTS:
Respond ONLY with a valid JSON array of objects. Do not include markdown ticks, backticks, or explanatory prose outside the JSON array.
Each JSON object must have the following fields:
- "priority": integer from 1 (highest urgency) to 5
- "title": short concise imperative action title (e.g. "Refactor OrderProcessor to Guard Against Cyclomatic Spikes")
- "category": one of ["Security", "Architecture", "Refactoring", "Testing", "Maintainability"]
- "description": clear explanation of why this is a risk and what data points support it
- "suggested_fix": concrete, actionable guidance on how the developer should solve it
- "file_path": relevant file path if specific, or empty string
- "impact": one of ["Critical", "High", "Medium", "Low"]
"""
            # Use modern google.genai SDK (with fallback for legacy environments)
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=self.api_key)
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config,
                )
                text = response.text.strip() if response.text else ""

            except ImportError:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=FutureWarning)
                    import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                model = legacy_genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                text = response.text.strip() if response.text else ""

            # Clean possible markdown wrapping
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:].strip()

            parsed = json.loads(text)
            recs = []
            for item in parsed[:5]:
                recs.append(RecommendationItem(
                    priority=item.get("priority", len(recs) + 1),
                    title=item.get("title", "Quality Improvement"),
                    category=item.get("category", "Maintainability"),
                    description=item.get("description", ""),
                    suggested_fix=item.get("suggested_fix", ""),
                    file_path=item.get("file_path", ""),
                    impact=item.get("impact", "Medium"),
                ))
            if recs:
                return recs
        except Exception as e:
            print(f"[GeminiProvider] Gemini API call error: {e}. Falling back to rule-based engine.")

        return self.fallback.generate_recommendations(metrics_summary, top_risky_files, findings)
