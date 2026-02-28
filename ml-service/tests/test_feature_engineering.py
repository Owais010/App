"""Unit tests for feature engineering module."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.feature_engineering import (
    compute_derived_features,
    prepare_feature_vector,
    get_feature_names,
    compute_gap_score_label,
    compute_difficulty_label,
    compute_engagement_score
)


class TestComputeDerivedFeatures:
    """Tests for compute_derived_features function."""
    
    def test_normal_input(self):
        """Test with typical input values."""
        input_data = {
            "attempt_count": 10,
            "correct_attempts": 7,
            "session_duration": 300.0,
            "previous_mastery_score": 0.6,
            "self_confidence_rating": 0.8,
            "difficulty_feedback": 3
        }
        result = compute_derived_features(input_data)
        
        assert "accuracy_rate" in result
        assert "failure_rate" in result
        assert "learning_velocity" in result
        assert "confidence_performance_gap" in result
        assert "difficulty_stress_index" in result
        assert "persistence_score" in result
        
        assert result["accuracy_rate"] == pytest.approx(0.7, rel=0.01)
        assert result["failure_rate"] == pytest.approx(0.3, rel=0.01)
        assert result["failure_rate"] == pytest.approx(1.0 - result["accuracy_rate"], rel=0.01)
    
    def test_zero_attempts(self):
        """Test handling of zero attempt_count (division by zero)."""
        input_data = {
            "attempt_count": 0,
            "correct_attempts": 0,
            "session_duration": 100.0,
            "previous_mastery_score": 0.5,
            "self_confidence_rating": 0.5,
            "difficulty_feedback": 3
        }
        result = compute_derived_features(input_data)
        
        assert result["accuracy_rate"] == 0.0
        assert result["failure_rate"] == 1.0
    
    def test_zero_session_duration(self):
        """Test handling of zero session_duration (division by zero)."""
        input_data = {
            "attempt_count": 5,
            "correct_attempts": 3,
            "session_duration": 0.0,
            "previous_mastery_score": 0.5,
            "self_confidence_rating": 0.5,
            "difficulty_feedback": 3
        }
        result = compute_derived_features(input_data)
        
        assert result["learning_velocity"] == 0.0
    
    def test_perfect_accuracy(self):
        """Test case with 100% accuracy."""
        input_data = {
            "attempt_count": 10,
            "correct_attempts": 10,
            "session_duration": 300.0,
            "previous_mastery_score": 0.9,
            "self_confidence_rating": 0.9,
            "difficulty_feedback": 2
        }
        result = compute_derived_features(input_data)
        
        assert result["accuracy_rate"] == 1.0
        assert result["failure_rate"] == 0.0
        assert result["difficulty_stress_index"] == 0.0


class TestPrepareFeatureVector:
    """Tests for prepare_feature_vector function."""
    
    def test_feature_count(self):
        """Test that feature vector has correct length."""
        input_data = {
            "attempt_count": 10,
            "correct_attempts": 7,
            "avg_response_time": 2.5,
            "self_confidence_rating": 0.8,
            "difficulty_feedback": 3,
            "session_duration": 300.0,
            "previous_mastery_score": 0.6,
            "time_since_last_attempt": 3600.0
        }
        
        vector, derived = prepare_feature_vector(input_data)
        feature_names = get_feature_names()
        
        # Shape is (1, 14) so check second dimension
        assert vector.shape[1] == len(feature_names)
        assert vector.shape[1] == 14

    def test_feature_order(self):
        """Test that features are in expected order."""
        input_data = {
            "attempt_count": 10,
            "correct_attempts": 7,
            "avg_response_time": 2.5,
            "self_confidence_rating": 0.8,
            "difficulty_feedback": 3,
            "session_duration": 300.0,
            "previous_mastery_score": 0.6,
            "time_since_last_attempt": 3600.0
        }
        
        vector, derived = prepare_feature_vector(input_data)
        
        # vector is shape (1, 14), access as vector[0]
        assert vector[0, 0] == 10       # attempt_count
        assert vector[0, 1] == 7        # correct_attempts
        assert vector[0, 2] == 2.5      # avg_response_time
        assert vector[0, 8] == pytest.approx(0.7, rel=0.01)  # accuracy_rate


class TestGetFeatureNames:
    """Tests for get_feature_names function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        names = get_feature_names()
        assert isinstance(names, list)
    
    def test_correct_count(self):
        """Test correct number of feature names."""
        names = get_feature_names()
        assert len(names) == 14
    
    def test_expected_names(self):
        """Test that expected names are present."""
        names = get_feature_names()
        assert "attempt_count" in names
        assert "accuracy_rate" in names
        assert "failure_rate" in names
        assert "persistence_score" in names


class TestComputeGapScoreLabel:
    """Tests for compute_gap_score_label function."""
    
    def test_high_gap(self):
        """Test high skill gap (struggling learner)."""
        derived = {"failure_rate": 0.8, "confidence_performance_gap": 0.5}
        gap = compute_gap_score_label(derived, previous_mastery_score=0.2)
        
        assert 0.0 <= gap <= 1.0
        assert gap > 0.5

    def test_low_gap(self):
        """Test low skill gap (proficient learner)."""
        derived = {"failure_rate": 0.1, "confidence_performance_gap": 0.1}
        gap = compute_gap_score_label(derived, previous_mastery_score=0.9)
        
        assert 0.0 <= gap <= 1.0
        assert gap < 0.3


class TestComputeDifficultyLabel:
    """Tests for compute_difficulty_label function."""
    
    def test_easy(self):
        """Test classification as easy."""
        label = compute_difficulty_label(accuracy_rate=0.9)
        assert label == 0
    
    def test_medium(self):
        """Test classification as medium."""
        label = compute_difficulty_label(accuracy_rate=0.6)
        assert label == 1
    
    def test_hard(self):
        """Test classification as hard."""
        label = compute_difficulty_label(accuracy_rate=0.3)
        assert label == 2
    
    def test_boundary_easy_medium(self):
        """Test boundary between easy and medium."""
        assert compute_difficulty_label(0.81) == 0
        assert compute_difficulty_label(0.80) == 1
    
    def test_boundary_medium_hard(self):
        """Test boundary between medium and hard."""
        assert compute_difficulty_label(0.50) == 1
        assert compute_difficulty_label(0.49) == 2


class TestComputeEngagementScore:
    """Tests for compute_engagement_score function."""
    
    def test_produces_valid_range(self):
        """Test that output is in valid range."""
        score = compute_engagement_score(
            accuracy_rate=0.7,
            persistence_score=10.0,
            gap_score=0.3
        )
        
        assert 0.0 <= score <= 1.0
    
    def test_high_performer(self):
        """Test high performer gets high score."""
        score = compute_engagement_score(
            accuracy_rate=0.95,
            persistence_score=50.0,  # Will be capped to 1.0 in normalization
            gap_score=0.1
        )
        
        assert score > 0.7
    
    def test_low_performer(self):
        """Test low performer gets low score.""" 
        score = compute_engagement_score(
            accuracy_rate=0.2,
            persistence_score=2.0,
            gap_score=0.8
        )
        
        assert score < 0.4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
