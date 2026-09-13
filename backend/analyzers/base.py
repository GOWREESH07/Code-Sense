from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class Finding(BaseModel):
    file_path: str
    line_number: int = 1
    rule_id: str
    severity: str = "info" # info, warning, error, critical
    tool: str
    description: str


class PluginResult(BaseModel):
    metrics: Dict[str, Any] = Field(default_factory=dict)
    findings: List[Finding] = Field(default_factory=list)


class AnalyzerPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        pass

    @abstractmethod
    def analyze(self, file_path: Path, content: str) -> PluginResult:
        """Analyze a single file and return metrics and findings."""
        pass
