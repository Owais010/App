"""
Pydantic schemas for request/response validation.

Defines all input and output data structures for the ML service API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class PredictionInput(BaseModel):
    """
    Input schema for prediction requests.
    
    All fields are required and validated for correct types and ranges.
    """
    user_id: str = Field(..., description="Unique identifier for the user")
    topic_id: str = Field(..., description="Unique identifier for the topic")
    attempt_count: int = Field(..., ge=1, description="Total number of attempts")
    correct_attempts: int = Field(..., ge=0, description="Number of correct attempts")
    avg_response_time: float = Field(..., ge=0, description="Average response time in seconds")
    self_confidence_rating: float = Field(..., ge=0, le=1, description="User's self-confidence rating (0-1)")
    difficulty_feedback: int = Field(..., ge=1, le=5, description="User's difficulty feedback (1-5)")
    session_duration: float = Field(..., gt=0, description="Session duration in minutes")
    previous_mastery_score: float = Field(..., ge=0, le=1, description="Previous mastery score (0-1)")
    time_since_last_attempt: float = Field(..., ge=0, description="Time since last attempt in hours")

    @field_validator('correct_attempts')
    @classmethod
    def correct_attempts_must_not_exceed_total(cls, v, info):
        """Validate that correct attempts don't exceed total attempts."""
        if 'attempt_count' in info.data and v > info.data['attempt_count']:
            raise ValueError('correct_attempts cannot exceed attempt_count')
        return v


class SkillGapOutput(BaseModel):
    """Output schema for skill gap estimation."""
    gap_score: float = Field(..., ge=0, le=1, description="Estimated skill gap score (0-1)")
    weak: bool = Field(..., description="True if gap_score > 0.6")


class DifficultyOutput(BaseModel):
    """Output schema for difficulty classification."""
    difficulty_level: Literal["easy", "medium", "hard"] = Field(
        ..., 
        description="Predicted difficulty level"
    )


class RankingOutput(BaseModel):
    """Output schema for recommendation ranking."""
    ranking_score: float = Field(..., description="Engagement success score for ranking")


class AdaptationOutput(BaseModel):
    """Output schema for adaptation signals."""
    action: Literal[
        "add_foundation_resources",
        "reduce_difficulty",
        "increase_difficulty",
        "continue_current_path"
    ] = Field(..., description="Recommended adaptation action")


class PredictionResponse(BaseModel):
    """
    Unified response schema combining all prediction outputs.
    """
    skill_gap: SkillGapOutput
    difficulty: DifficultyOutput
    ranking: RankingOutput
    adaptation: AdaptationOutput
    request_id: str = Field(..., description="Unique identifier for the request")
    prediction_time_ms: float = Field(..., description="Time taken for prediction in milliseconds")


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service health status")
    models_loaded: bool = Field(..., description="Whether all models are loaded")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    request_id: str = Field(default=None, description="Request identifier if available")
