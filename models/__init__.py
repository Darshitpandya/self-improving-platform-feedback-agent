from __future__ import annotations

from pydantic import BaseModel, Field


class FrictionSignal(BaseModel):
    source: str = Field(description="Signal source: git_removals, ci_friction, scorecard_trends, pr_comments")
    detail: str = Field(description="What the signal detected")


class ImprovementProposal(BaseModel):
    title: str = Field(description="Short proposal title, e.g. 'Make logging sidecar optional'")
    golden_path_step: str = Field(description="Which golden path step is causing friction")
    problem: str = Field(description="What friction was detected and how widespread it is")
    recommendation: str = Field(description="Specific action to take")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    estimated_impact: str = Field(description="Expected impact on adoption or developer experience")
    evidence: list[FrictionSignal] = Field(description="Signals that support this proposal")
