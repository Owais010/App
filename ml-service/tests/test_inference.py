"""Unit tests for inference module."""

import pytest
import numpy as np
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.inference import (
    determine_adaptation_action,
    run_inference
)
from app.schemas import PredictionInput


class TestDetermineAdaptationAction:
    """Tests for the determine_adaptation_action function."""
    
    def test_high_gap_returns_add_foundation(self):
        """High gap score triggers foundation resources."""
        action = determine_adaptation_action(
            gap_score=0.8,
            difficulty_level="hard",
            accuracy_rate=0.3,
            failure_rate=0.7
        )
        assert action == "add_foundation_resources"
    
    def test_hard_difficulty_high_failure_returns_reduce(self):
        """Hard difficulty with high failure triggers difficulty reduction."""
        action = determine_adaptation_action(
            gap_score=0.4,  # Not high enough to trigger add_foundation
            difficulty_level="hard",
            accuracy_rate=0.3,
            failure_rate=0.7
        )
        assert action == "reduce_difficulty"
    
    def test_high_accuracy_returns_increase_difficulty(self):
        """High accuracy triggers difficulty increase."""
        action = determine_adaptation_action(
            gap_score=0.2,
            difficulty_level="easy",
            accuracy_rate=0.9,
            failure_rate=0.1
        )
        assert action == "increase_difficulty"
    
    def test_default_continue_current_path(self):
        """Medium conditions continue current path."""
        action = determine_adaptation_action(
            gap_score=0.4,
            difficulty_level="medium",
            accuracy_rate=0.6,
            failure_rate=0.4
        )
        assert action == "continue_current_path"


class TestPredictFunctions:
    """Tests for prediction functions - skipped as they require loaded models."""
    
    @pytest.mark.skip(reason="Requires loaded model infrastructure")
    def test_predict_skill_gap_clips_output(self):
        """Test that skill gap prediction is clipped to [0, 1]."""
        pass
    
    @pytest.mark.skip(reason="Requires loaded model infrastructure")
    def test_predict_skill_gap_clips_negative(self):
        """Test that negative skill gap prediction is clipped to 0."""
        pass
    
    @pytest.mark.skip(reason="Requires loaded model infrastructure")
    def test_predict_difficulty_returns_string(self):
        """Test that difficulty prediction returns string."""
        pass
    
    @pytest.mark.skip(reason="Requires loaded model infrastructure")
    def test_predict_ranking_clips_output(self):
        """Test that ranking prediction is clipped to [0, 1]."""
        pass


class TestRunInference:
    """Integration tests for run_inference function."""
    
    @pytest.fixture
    def sample_input_dict(self):
        """Create a sample input dictionary."""
        return {
            "user_id": "test-123",
            "topic_id": "topic-456",
            "attempt_count": 10,
            "correct_attempts": 7,
            "avg_response_time": 2.5,
            "self_confidence_rating": 0.8,
            "difficulty_feedback": 3,
            "session_duration": 300.0,
            "previous_mastery_score": 0.6,
            "time_since_last_attempt": 3600.0
        }
    
    @pytest.mark.skip(reason="Requires model loader infrastructure")
    def test_run_inference_returns_all_fields(self, sample_input_dict):
        """Test that run_inference returns all expected fields."""
        # Skipped - requires actual model loader
        pass
    
    @pytest.mark.skip(reason="Requires model loader infrastructure")
    def test_run_inference_preserves_ids(self, sample_input_dict):
        """Test that user_id and topic_id are preserved."""
        # Skipped - requires actual model loader
        pass
    
    @pytest.mark.skip(reason="Requires model loader infrastructure")
    def test_run_inference_valid_ranges(self, sample_input_dict):
        """Test that predictions are in valid ranges."""
        # Skipped - requires actual model loader
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
