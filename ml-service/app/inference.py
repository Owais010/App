"""
Inference Engine — Predict levels, difficulty, and next-question success.

Implements the dual-track architecture:
  - Rules-based baseline (always available, Phase 2)
  - ML models (when trained & loaded, Phase 6+)

Automatically falls back to rules when:
  - Models aren't loaded yet (pre-training)
  - User has too few answers (cold start)
  - ML confidence is too low
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np

from app.config import get_settings
from app.feature_engineering import (
    FEATURE_NAMES,
    FeatureVector,
    feature_vector_to_array,
    get_features,
)
from app.model_loader import registry
from app.schemas import (
    DifficultyResponse,
    LevelPredictionResponse,
    NextQuestionResponse,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# METRICS (simple counters for monitoring)
# ─────────────────────────────────────────────────────────────────────────────

_prediction_counts: dict[str, int] = {
    "level_rules": 0,
    "level_ml": 0,
    "difficulty_rules": 0,
    "difficulty_ml": 0,
}
_latency_sums: dict[str, float] = {}


def get_prediction_stats() -> dict:
    """Return prediction counts and average latencies."""
    return {
        "counts": dict(_prediction_counts),
        "avg_latency_ms": {
            k: round(v / max(_prediction_counts.get(k, 1), 1) * 1000, 2)
            for k, v in _latency_sums.items()
        },
    }


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  RULES-BASED BASELINE (Phase 2)                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


def _rules_classify_level(fv: FeatureVector) -> LevelPredictionResponse:
    """
    Rules-based level classification.

    Uses Laplace-smoothed accuracy with configurable thresholds:
      - accuracy < 0.5  → beginner
      - accuracy < 0.75 → intermediate
      - accuracy >= 0.75 → advanced

    Minimum 5 attempts before trusting (otherwise beginner).
    """
    settings = get_settings()
    alpha = settings.SMOOTHING_ALPHA

    # Laplace-smoothed accuracy
    smoothed = (fv.correct_attempts + alpha) / (
        fv.total_attempts + 2 * alpha
    )

    # Confidence grows with attempts
    confidence = min(1.0, fv.total_attempts / (settings.MIN_ATTEMPTS * 2))

    if fv.total_attempts < settings.MIN_ATTEMPTS:
        level = "beginner"
        probs = {"beginner": 0.8, "intermediate": 0.15, "advanced": 0.05}
    elif smoothed < settings.INTERMEDIATE_THRESHOLD:
        level = "beginner"
        probs = {"beginner": 0.7, "intermediate": 0.2, "advanced": 0.1}
    elif smoothed < settings.ADVANCED_THRESHOLD:
        level = "intermediate"
        probs = {"beginner": 0.1, "intermediate": 0.7, "advanced": 0.2}
    else:
        level = "advanced"
        probs = {"beginner": 0.05, "intermediate": 0.15, "advanced": 0.8}

    return LevelPredictionResponse(
        predicted_level=level,
        confidence=round(confidence, 4),
        probabilities=probs,
        model_used="rules",
        features_used=fv,
    )


def _rules_recommend_difficulty(
    fv: FeatureVector,
) -> DifficultyResponse:
    """
    Rules-based difficulty recommendation.

    Maps level to difficulty with adjustment for trends:
      beginner    → easy   (medium if improving)
      intermediate→ medium (hard if improving, easy if declining)
      advanced    → hard   (medium if declining)
    """
    settings = get_settings()

    # Base level
    if fv.total_attempts < settings.MIN_ATTEMPTS:
        return DifficultyResponse(
            recommended_difficulty="easy",
            predicted_success_prob=0.7,
            confidence=0.3,
            model_used="rules",
            difficulty_probs={"easy": 0.6, "medium": 0.3, "hard": 0.1},
        )

    # Determine base level from accuracy
    smoothed = (fv.correct_attempts + settings.SMOOTHING_ALPHA) / (
        fv.total_attempts + 2 * settings.SMOOTHING_ALPHA
    )

    if smoothed < settings.INTERMEDIATE_THRESHOLD:
        base = "easy"
    elif smoothed < settings.ADVANCED_THRESHOLD:
        base = "medium"
    else:
        base = "hard"

    # Trend adjustment: if improving, nudge harder; if declining, nudge easier
    trend = fv.accuracy_trend
    if trend > 0.1 and base == "easy":
        base = "medium"
    elif trend > 0.1 and base == "medium":
        base = "hard"
    elif trend < -0.1 and base == "hard":
        base = "medium"
    elif trend < -0.1 and base == "medium":
        base = "easy"

    # Estimate success probability
    diff_acc_map = {
        "easy": fv.easy_accuracy,
        "medium": fv.medium_accuracy,
        "hard": fv.hard_accuracy,
    }
    pred_success = diff_acc_map.get(base, fv.accuracy)
    if pred_success == 0 and fv.total_attempts > 0:
        # No data at this difficulty; estimate from overall
        pred_success = fv.accuracy * {"easy": 1.2, "medium": 1.0, "hard": 0.7}[base]
        pred_success = min(pred_success, 1.0)

    confidence = min(1.0, fv.total_attempts / (settings.MIN_ATTEMPTS * 2))

    # Probability distribution
    probs = {"easy": 0.0, "medium": 0.0, "hard": 0.0}
    probs[base] = 0.6
    remaining = [d for d in probs if d != base]
    for r in remaining:
        probs[r] = 0.2

    return DifficultyResponse(
        recommended_difficulty=base,
        predicted_success_prob=round(pred_success, 4),
        confidence=round(confidence, 4),
        model_used="rules",
        difficulty_probs=probs,
    )


def _rules_next_question(
    fv: FeatureVector,
    candidate_difficulties: list[str],
) -> NextQuestionResponse:
    """
    Rules-based next-question success predictor.

    Estimates P(correct) per difficulty using per-difficulty accuracy
    with fallback to scaled overall accuracy.
    Target: ~70% success rate for optimal learning (Zone of Proximal Development).
    """
    settings = get_settings()

    scale = {"easy": 1.2, "medium": 1.0, "hard": 0.7}
    diff_acc = {
        "easy": fv.easy_accuracy,
        "medium": fv.medium_accuracy,
        "hard": fv.hard_accuracy,
    }

    probs: dict[str, float] = {}
    for diff in candidate_difficulties:
        if diff_acc.get(diff, 0) > 0:
            probs[diff] = round(min(diff_acc[diff], 1.0), 4)
        else:
            probs[diff] = round(
                min(fv.accuracy * scale.get(diff, 1.0), 1.0), 4
            )

    # Pick difficulty closest to 70% success
    target = 0.70
    optimal = min(probs, key=lambda d: abs(probs[d] - target))

    confidence = min(1.0, fv.total_attempts / (settings.MIN_ATTEMPTS * 2))

    return NextQuestionResponse(
        success_probabilities=probs,
        optimal_difficulty=optimal,
        confidence=round(confidence, 4),
        model_used="rules",
    )


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  ML-BASED PREDICTIONS (Phase 6+)                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


def _ml_classify_level(fv: FeatureVector) -> Optional[LevelPredictionResponse]:
    """
    ML-based level classification using XGBoost.

    Returns None if model isn't loaded (triggers rules fallback).
    """
    loaded = registry.get_model("level_classifier")
    if loaded is None:
        return None

    try:
        X = feature_vector_to_array(fv).reshape(1, -1)
        model = loaded.model

        # Get probabilities
        proba = model.predict_proba(X)[0]
        pred_idx = int(np.argmax(proba))

        # Decode label
        if loaded.label_encoder:
            classes = loaded.label_encoder.classes_
        else:
            classes = np.array(["beginner", "intermediate", "advanced"])

        predicted_level = str(classes[pred_idx])
        confidence = float(proba[pred_idx])

        probs = {
            str(classes[i]): round(float(proba[i]), 4)
            for i in range(len(classes))
        }

        return LevelPredictionResponse(
            predicted_level=predicted_level,
            confidence=round(confidence, 4),
            probabilities=probs,
            model_used=f"xgboost_v{loaded.version}",
            features_used=fv,
        )

    except Exception as e:
        logger.error("ML level classification failed: %s", e)
        return None


def _ml_recommend_difficulty(
    fv: FeatureVector,
) -> Optional[DifficultyResponse]:
    """
    ML-based difficulty recommendation using LightGBM.

    Returns None if model isn't loaded.
    """
    loaded = registry.get_model("difficulty_recommender")
    if loaded is None:
        return None

    try:
        X = feature_vector_to_array(fv).reshape(1, -1)
        model = loaded.model

        proba = model.predict_proba(X)[0]
        pred_idx = int(np.argmax(proba))

        if loaded.label_encoder:
            classes = loaded.label_encoder.classes_
        else:
            classes = np.array(["easy", "medium", "hard"])

        recommended = str(classes[pred_idx])
        confidence = float(proba[pred_idx])

        probs = {
            str(classes[i]): round(float(proba[i]), 4)
            for i in range(len(classes))
        }

        # Estimate success prob from per-difficulty accuracy
        diff_acc = {
            "easy": fv.easy_accuracy,
            "medium": fv.medium_accuracy,
            "hard": fv.hard_accuracy,
        }
        pred_success = diff_acc.get(recommended, fv.accuracy)

        return DifficultyResponse(
            recommended_difficulty=recommended,
            predicted_success_prob=round(pred_success, 4),
            confidence=round(confidence, 4),
            model_used=f"lightgbm_v{loaded.version}",
            difficulty_probs=probs,
        )

    except Exception as e:
        logger.error("ML difficulty recommendation failed: %s", e)
        return None


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  PUBLIC PREDICTION API                                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


async def predict_level(
    user_id: str,
    topic_id: str,
    precomputed_features: Optional[FeatureVector] = None,
) -> LevelPredictionResponse:
    """
    Predict user level for a topic.

    Uses ML model if available and user has enough data,
    otherwise falls back to rules.
    """
    t0 = time.time()
    settings = get_settings()

    fv = await get_features(user_id, topic_id, precomputed_features)

    # Try ML first if user has enough data
    if fv.total_attempts >= settings.MIN_ANSWERS_FOR_ML:
        ml_result = _ml_classify_level(fv)
        if ml_result is not None:
            _prediction_counts["level_ml"] = (
                _prediction_counts.get("level_ml", 0) + 1
            )
            _latency_sums["level_ml"] = (
                _latency_sums.get("level_ml", 0) + (time.time() - t0)
            )
            return ml_result

    # Fall back to rules
    result = _rules_classify_level(fv)
    _prediction_counts["level_rules"] = (
        _prediction_counts.get("level_rules", 0) + 1
    )
    _latency_sums["level_rules"] = (
        _latency_sums.get("level_rules", 0) + (time.time() - t0)
    )
    return result


async def predict_difficulty(
    user_id: str,
    topic_id: str,
    precomputed_features: Optional[FeatureVector] = None,
) -> DifficultyResponse:
    """Predict recommended difficulty for next question."""
    t0 = time.time()
    settings = get_settings()

    fv = await get_features(user_id, topic_id, precomputed_features)

    if fv.total_attempts >= settings.MIN_ANSWERS_FOR_ML:
        ml_result = _ml_recommend_difficulty(fv)
        if ml_result is not None:
            _prediction_counts["difficulty_ml"] = (
                _prediction_counts.get("difficulty_ml", 0) + 1
            )
            _latency_sums["difficulty_ml"] = (
                _latency_sums.get("difficulty_ml", 0) + (time.time() - t0)
            )
            return ml_result

    result = _rules_recommend_difficulty(fv)
    _prediction_counts["difficulty_rules"] = (
        _prediction_counts.get("difficulty_rules", 0) + 1
    )
    _latency_sums["difficulty_rules"] = (
        _latency_sums.get("difficulty_rules", 0) + (time.time() - t0)
    )
    return result


async def predict_next_question(
    user_id: str,
    topic_id: str,
    candidate_difficulties: list[str] | None = None,
    precomputed_features: Optional[FeatureVector] = None,
) -> NextQuestionResponse:
    """Predict success probability per difficulty for next question."""
    if candidate_difficulties is None:
        candidate_difficulties = ["easy", "medium", "hard"]

    fv = await get_features(user_id, topic_id, precomputed_features)
    return _rules_next_question(fv, candidate_difficulties)
