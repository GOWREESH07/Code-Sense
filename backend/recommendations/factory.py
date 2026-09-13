import os
from dotenv import load_dotenv
from backend.recommendations.base import RecommendationProvider
from backend.recommendations.rule_provider import RuleBasedRecommendationProvider
from backend.recommendations.gemini_provider import GeminiRecommendationProvider

load_dotenv()


def get_recommendation_provider() -> RecommendationProvider:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        print("[Recommendations] Gemini API key detected, using Gemini provider.")
        return GeminiRecommendationProvider(api_key=api_key)
    else:
        print("[Recommendations] No Gemini API key detected, using Rule-based provider.")
        return RuleBasedRecommendationProvider()
