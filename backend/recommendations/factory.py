import os
from pathlib import Path
from dotenv import load_dotenv
from backend.recommendations.base import RecommendationProvider
from backend.recommendations.rule_provider import RuleBasedRecommendationProvider
from backend.recommendations.gemini_provider import GeminiRecommendationProvider

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _BACKEND_DIR.parent
_ENV_CANDIDATES = [_BACKEND_DIR / ".env", _ROOT_DIR / ".env"]


def _load_env():
    for env_path in _ENV_CANDIDATES:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)


# Load at import time
_load_env()


def get_recommendation_provider() -> RecommendationProvider:
    # Refresh in case .env was edited while the server was running
    _load_env()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        print(f"[Recommendations] Gemini API key detected ({api_key[:6]}...{api_key[-4:]}), using GeminiRecommendationProvider.")
        return GeminiRecommendationProvider(api_key=api_key)
    else:
        print("[Recommendations] No Gemini API key detected in environment or .env, using RuleBasedRecommendationProvider.")
        return RuleBasedRecommendationProvider()

