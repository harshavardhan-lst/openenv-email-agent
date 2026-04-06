"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class UserResponse(BaseModel):
    id: str
    name: str
    total_rewards: int = 0


class TaskCreate(BaseModel):
    user_id: str
    summary: str = Field(..., min_length=1, max_length=8000)


class TaskSubmitResponse(BaseModel):
    message: str
    task_id: str


class QuizSubmit(BaseModel):
    task_id: str
    questions: List[Any]
    answers: List[str]
    time_taken: int = Field(..., ge=0)
    attempts: int = Field(1, ge=1)
    # Client may send hints; server recomputes from DB when possible
    avg_user_score: int = Field(0, ge=0, le=30)
    tasks_completed_today: int = Field(0, ge=0)
    account_age_days: int = Field(0, ge=0)
    previous_rewards: int = Field(0, ge=0)
    time_of_day: int = Field(0, ge=0, le=23)


class QuizResultResponse(BaseModel):
    score: int
    fraud_probability: float
    passed: bool
    reward_granted: bool
    explanation: str
    task_similarity: float
