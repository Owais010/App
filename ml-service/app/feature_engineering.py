"""
Feature Engineering module for the Adaptive Learning Intelligence Engine.

Contains all feature derivation and transformation logic.
All operations are deterministic with no randomness.
"""

import numpy as np
from typing import Dict, Any, Tuple


def compute_derived_features(input_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute all derived features from raw input data.
    
    Args:
        input_data: Dictionary containing raw input fields from the request.
        
    Returns:
        Dictionary containing all derived feature values.
    """
    # Extract base values
    attempt_count = input_data["attempt_count"]
    correct_attempts = input_data["correct_attempts"]
    session_duration = input_data["session_duration"]
    previous_mastery_score = input_data["previous_mastery_score"]
    self_confidence_rating = input_data["self_confidence_rating"]
    difficulty_feedback = input_data["difficulty_feedback"]
    
    # Compute derived features
    accuracy_rate = correct_attempts / attempt_count if attempt_count > 0 else 0.0
    failure_rate = 1.0 - accuracy_rate
    
    # Learning velocity: mastery progress relative to time spent
    learning_velocity = previous_mastery_score / session_duration if session_duration > 0 else 0.0
    
    # Gap between self-perception and actual performance
    confidence_performance_gap = self_confidence_rating - accuracy_rate
    
    # Stress indicator combining perceived difficulty with actual failures
    difficulty_stress_index = difficulty_feedback * failure_rate
    
    # Measure of sustained effort
    persistence_score = session_duration / (attempt_count + 1)
    
    return {
        "accuracy_rate": accuracy_rate,
        "failure_rate": failure_rate,
        "learning_velocity": learning_velocity,
        "confidence_performance_gap": confidence_performance_gap,
        "difficulty_stress_index": difficulty_stress_index,
        "persistence_score": persistence_score
    }


def prepare_feature_vector(input_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Prepare the complete feature vector for model prediction.
    
    Combines raw input features with derived features into a numpy array
    suitable for sklearn model prediction.
    
    Args:
        input_data: Dictionary containing raw input fields from the request.
        
    Returns:
        Tuple of (feature_vector as numpy array, derived_features dict)
    """
    # Compute derived features
    derived = compute_derived_features(input_data)
    
    # Build feature vector in consistent order
    # Order: raw features first, then derived features
    feature_vector = np.array([
        input_data["attempt_count"],
        input_data["correct_attempts"],
        input_data["avg_response_time"],
        input_data["self_confidence_rating"],
        input_data["difficulty_feedback"],
        input_data["session_duration"],
        input_data["previous_mastery_score"],
        input_data["time_since_last_attempt"],
        derived["accuracy_rate"],
        derived["failure_rate"],
        derived["learning_velocity"],
        derived["confidence_performance_gap"],
        derived["difficulty_stress_index"],
        derived["persistence_score"]
    ], dtype=np.float64).reshape(1, -1)
    
    return feature_vector, derived


def get_feature_names() -> list:
    """
    Get the ordered list of feature names.
    
    Returns:
        List of feature names in the same order as the feature vector.
    """
    return [
        "attempt_count",
        "correct_attempts",
        "avg_response_time",
        "self_confidence_rating",
        "difficulty_feedback",
        "session_duration",
        "previous_mastery_score",
        "time_since_last_attempt",
        "accuracy_rate",
        "failure_rate",
        "learning_velocity",
        "confidence_performance_gap",
        "difficulty_stress_index",
        "persistence_score"
    ]


def compute_gap_score_label(derived_features: Dict[str, float], previous_mastery_score: float) -> float:
    """
    Compute the skill gap score label for training.
    
    Formula:
        gap_score = 0.5 * failure_rate + 
                    0.3 * (1 - previous_mastery_score) + 
                    0.2 * abs(confidence_performance_gap)
    
    Args:
        derived_features: Dictionary of derived feature values.
        previous_mastery_score: The user's previous mastery score.
        
    Returns:
        Gap score value between 0 and 1.
    """
    gap_score = (
        0.5 * derived_features["failure_rate"] +
        0.3 * (1.0 - previous_mastery_score) +
        0.2 * abs(derived_features["confidence_performance_gap"])
    )
    # Clamp to [0, 1]
    return max(0.0, min(1.0, gap_score))


def compute_difficulty_label(accuracy_rate: float) -> int:
    """
    Compute the difficulty classification label for training.
    
    Rules:
        - accuracy_rate > 0.8 → easy (0)
        - 0.5 <= accuracy_rate <= 0.8 → medium (1)
        - accuracy_rate < 0.5 → hard (2)
    
    Args:
        accuracy_rate: The computed accuracy rate.
        
    Returns:
        Difficulty label (0=easy, 1=medium, 2=hard).
    """
    if accuracy_rate > 0.8:
        return 0  # easy
    elif accuracy_rate >= 0.5:
        return 1  # medium
    else:
        return 2  # hard


def compute_engagement_score(
    accuracy_rate: float,
    persistence_score: float,
    gap_score: float
) -> float:
    """
    Compute the engagement success score for ranking model training.
    
    Formula:
        engagement_score = 0.4 * accuracy_rate + 
                          0.3 * persistence_score + 
                          0.3 * (1 - gap_score)
    
    Args:
        accuracy_rate: The computed accuracy rate.
        persistence_score: The computed persistence score.
        gap_score: The computed gap score.
        
    Returns:
        Engagement success score.
    """
    # Normalize persistence score to [0, 1] range for balanced contribution
    # Typical persistence scores range from 0 to ~10, so we cap at 10
    normalized_persistence = min(persistence_score / 10.0, 1.0)
    
    engagement_score = (
        0.4 * accuracy_rate +
        0.3 * normalized_persistence +
        0.3 * (1.0 - gap_score)
    )
    return engagement_score
