"""
Pydantic Schemas — Request/response models for the ML API.

Every payload is validated here before reaching inference code.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FEATURE VECTOR                                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class FeatureVector(BaseModel):
    """
    14-dimensional feature vector matching `compute_ml_features` RPC.
    """
    total_attempts: int = Field(0, ge=0)
    correct_attempts: int = Field(0, ge=0)
    accuracy: float = Field(0.0, ge=0.0, le=1.0)
    weighted_score: float = Field(0.0, ge=0.0)
    recent_accuracy: float = Field(0.0, ge=0.0, le=1.0)
    accuracy_trend: float = Field(0.0, ge=-1.0, le=1.0)
    streak_length: int = Field(0, ge=0)
    avg_time_per_q: float = Field(0.0, ge=0.0)
    days_since_last: float = Field(-1.0)
    easy_accuracy: float = Field(0.0, ge=0.0, le=1.0)
    medium_accuracy: float = Field(0.0, ge=0.0, le=1.0)
    hard_accuracy: float = Field(0.0, ge=0.0, le=1.0)
    global_accuracy: float = Field(0.0, ge=0.0, le=1.0)
    topics_attempted: int = Field(0, ge=0)


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  LEVEL PREDICTION                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class LevelPredictionRequest(BaseModel):
    user_id: str
    topic_id: str
    features: Optional[FeatureVector] = None  # If omitted, fetched from DB


class LevelPredictionResponse(BaseModel):
    predicted_level: str  # beginner | intermediate | advanced
    confidence: float
    probabilities: dict[str, float]  # {"beginner": 0.1, "intermediate": 0.3, "advanced": 0.6}
    model_used: str  # "rules" | "xgboost_v1"
    features_used: Optional[FeatureVector] = None


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  DIFFICULTY RECOMMENDATION                                              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class DifficultyRequest(BaseModel):
    user_id: str
    topic_id: str
    features: Optional[FeatureVector] = None


class DifficultyResponse(BaseModel):
    recommended_difficulty: str  # easy | medium | hard
    predicted_success_prob: float
    confidence: float
    model_used: str
    difficulty_probs: dict[str, float]


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  NEXT QUESTION PREDICTION                                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class NextQuestionRequest(BaseModel):
    user_id: str
    topic_id: str
    candidate_difficulties: list[str] = ["easy", "medium", "hard"]
    features: Optional[FeatureVector] = None


class NextQuestionResponse(BaseModel):
    success_probabilities: dict[str, float]  # per difficulty
    optimal_difficulty: str  # targets ~70% success rate
    confidence: float
    model_used: str


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  BATCH PREDICTION                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class BatchPredictionRequest(BaseModel):
    user_id: str
    topic_ids: list[str]


class TopicPrediction(BaseModel):
    topic_id: str
    predicted_level: str
    confidence: float
    recommended_difficulty: str
    predicted_success_prob: float


class BatchPredictionResponse(BaseModel):
    predictions: list[TopicPrediction]
    model_used: str


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  GENERIC PREDICT (backward compat with existing mlService.js client)    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class GenericPredictRequest(BaseModel):
    """Matches the payload from src/lib/mlService.js `getMLPrediction()`."""
    user_id: Optional[str] = None
    topic_id: Optional[str] = None
    features: Optional[dict] = None
    prediction_type: str = "level"  # level | difficulty | next_question


class GenericPredictResponse(BaseModel):
    prediction: dict
    model_used: str
    confidence: float


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  HEALTH / MONITORING                                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

class HealthResponse(BaseModel):
    status: str
    models_loaded: dict[str, bool]
    version: str


class ModelMetrics(BaseModel):
    model_name: str
    version: str
    accuracy: Optional[float] = None
    f1: Optional[float] = None
    auc: Optional[float] = None
    predictions_served: int = 0
    avg_latency_ms: float = 0.0
