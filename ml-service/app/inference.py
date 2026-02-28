"""
Inference module for the Adaptive Learning Intelligence Engine.

Contains all prediction logic and adaptation signal generation.
"""

import logging
from typing import Dict, Any, Tuple

import numpy as np

from app.feature_engineering import prepare_feature_vector
from app.model_loader import get_model_loader
from app.config import (
    SKILL_GAP_WEAK_THRESHOLD,
    ADAPTATION_GAP_HIGH_THRESHOLD,
    ADAPTATION_ACCURACY_HIGH_THRESHOLD,
    ADAPTATION_FAILURE_HIGH_THRESHOLD,
    DIFFICULTY_LABELS
)


logger = logging.getLogger(__name__)


def predict_skill_gap(feature_vector: np.ndarray) -> Tuple[float, bool]:
    """
    Predict skill gap score using the regression model.
    
    Args:
        feature_vector: Prepared feature vector as numpy array.
        
    Returns:
        Tuple of (gap_score, is_weak).
    """
    model_loader = get_model_loader()
    skill_gap_model = model_loader.skill_gap_model
    
    # Predict gap score
    gap_score = float(skill_gap_model.predict(feature_vector)[0])
    
    # Clamp to valid range [0, 1]
    gap_score = max(0.0, min(1.0, gap_score))
    
    # Determine if weak based on threshold
    is_weak = gap_score > SKILL_GAP_WEAK_THRESHOLD
    
    logger.debug(f"Skill gap prediction: score={gap_score:.4f}, weak={is_weak}")
    
    return gap_score, is_weak


def predict_difficulty(feature_vector: np.ndarray) -> str:
    """
    Predict difficulty level using the classification model.
    
    Args:
        feature_vector: Prepared feature vector as numpy array.
        
    Returns:
        Difficulty level string ("easy", "medium", or "hard").
    """
    model_loader = get_model_loader()
    difficulty_model = model_loader.difficulty_model
    
    # Predict difficulty class
    difficulty_class = int(difficulty_model.predict(feature_vector)[0])
    
    # Convert to label
    difficulty_level = DIFFICULTY_LABELS.get(difficulty_class, "medium")
    
    logger.debug(f"Difficulty prediction: class={difficulty_class}, level={difficulty_level}")
    
    return difficulty_level


def predict_ranking(feature_vector: np.ndarray) -> float:
    """
    Predict engagement ranking score using the scoring model.
    
    Args:
        feature_vector: Prepared feature vector as numpy array.
        
    Returns:
        Ranking score as float, clamped to [0, 1] range.
    """
    model_loader = get_model_loader()
    ranking_model = model_loader.ranking_model
    
    # Predict ranking score
    ranking_score = float(ranking_model.predict(feature_vector)[0])
    
    # Clamp to valid range [0, 1]
    ranking_score = max(0.0, min(1.0, ranking_score))
    
    logger.debug(f"Ranking prediction: score={ranking_score:.4f}")
    
    return ranking_score


def determine_adaptation_action(
    gap_score: float,
    difficulty_level: str,
    accuracy_rate: float,
    failure_rate: float
) -> str:
    """
    Determine the adaptation action based on prediction results.
    
    Rules (in order of priority):
        1. If gap_score > 0.75 → "add_foundation_resources"
        2. If difficulty == "hard" AND failure_rate > 0.6 → "reduce_difficulty"
        3. If accuracy_rate > 0.85 → "increase_difficulty"
        4. Else → "continue_current_path"
    
    Args:
        gap_score: Predicted skill gap score.
        difficulty_level: Predicted difficulty level.
        accuracy_rate: Computed accuracy rate.
        failure_rate: Computed failure rate.
        
    Returns:
        Adaptation action string.
    """
    # Rule 1: High skill gap indicates need for foundational support
    if gap_score > ADAPTATION_GAP_HIGH_THRESHOLD:
        action = "add_foundation_resources"
        logger.debug(f"Adaptation: {action} (gap_score={gap_score:.4f} > {ADAPTATION_GAP_HIGH_THRESHOLD})")
        return action
    
    # Rule 2: Hard content with high failure needs difficulty reduction
    if difficulty_level == "hard" and failure_rate > ADAPTATION_FAILURE_HIGH_THRESHOLD:
        action = "reduce_difficulty"
        logger.debug(f"Adaptation: {action} (difficulty=hard, failure_rate={failure_rate:.4f})")
        return action
    
    # Rule 3: High accuracy indicates readiness for more challenge
    if accuracy_rate > ADAPTATION_ACCURACY_HIGH_THRESHOLD:
        action = "increase_difficulty"
        logger.debug(f"Adaptation: {action} (accuracy_rate={accuracy_rate:.4f} > {ADAPTATION_ACCURACY_HIGH_THRESHOLD})")
        return action
    
    # Default: Continue on current path
    action = "continue_current_path"
    logger.debug(f"Adaptation: {action} (default)")
    return action


def run_inference(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete inference pipeline.
    
    Flow:
        1. Prepare feature vector
        2. Run all model predictions
        3. Determine adaptation action
        4. Return unified response
    
    Args:
        input_data: Validated input data dictionary.
        
    Returns:
        Dictionary containing all prediction results.
    """
    logger.info(f"Running inference for user={input_data.get('user_id')}, topic={input_data.get('topic_id')}")
    
    # Step 1: Feature engineering
    feature_vector, derived_features = prepare_feature_vector(input_data)
    
    # Step 2: Run predictions
    gap_score, is_weak = predict_skill_gap(feature_vector)
    difficulty_level = predict_difficulty(feature_vector)
    ranking_score = predict_ranking(feature_vector)
    
    # Step 3: Determine adaptation action
    adaptation_action = determine_adaptation_action(
        gap_score=gap_score,
        difficulty_level=difficulty_level,
        accuracy_rate=derived_features["accuracy_rate"],
        failure_rate=derived_features["failure_rate"]
    )
    
    # Step 4: Build response
    result = {
        "skill_gap": {
            "gap_score": round(gap_score, 4),
            "weak": is_weak
        },
        "difficulty": {
            "difficulty_level": difficulty_level
        },
        "ranking": {
            "ranking_score": round(ranking_score, 4)
        },
        "adaptation": {
            "action": adaptation_action
        }
    }
    
    logger.info(f"Inference complete: gap={gap_score:.4f}, difficulty={difficulty_level}, "
                f"ranking={ranking_score:.4f}, action={adaptation_action}")
    
    return result
