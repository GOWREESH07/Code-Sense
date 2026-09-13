from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    priority: int = Field(ge=1, le=5, description="Priority rank 1 (highest) to 5")
    title: str
    category: str # Security, Architecture, Refactoring, Testing, Maintainability
    description: str
    suggested_fix: str
    file_path: str = ""
    impact: str # Critical, High, Medium, Low


class RecommendationProvider(ABC):
    @abstractmethod
    def generate_recommendations(
        self,
        metrics_summary: Dict[str, Any],
        top_risky_files: List[Dict[str, Any]],
        findings: List[Any],
    ) -> List[RecommendationItem]:
        pass
