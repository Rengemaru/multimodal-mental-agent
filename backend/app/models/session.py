from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class TurnLog(BaseModel):
    turn: int
    question: str
    answer: str
    mental_state: str
    mental_score: float
    score_breakdown: dict
    metrics: dict


class SessionLog(BaseModel):
    session_id: str
    subject_id: str
    consent_version: str
    self_report: dict
    weights_used: dict
    weight_mode: Literal["fixed", "dynamic", "learned"]
    turns: list[TurnLog] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
