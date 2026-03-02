"""
Tests for Inference Engine — both rules and ML predictions.
"""

import pytest

from app.inference import (
    _rules_classify_level,
    _rules_next_question,
    _rules_recommend_difficulty,
)
from app.schemas import FeatureVector


class TestRulesLevelClassification:
    """Test rules-based level classification (Phase 2 baseline)."""

    def test_cold_start_returns_beginner(self, cold_start_features):
        result = _rules_classify_level(cold_start_features)
        assert result.predicted_level == "beginner"
        assert result.model_used == "rules"

    def test_low_accuracy_returns_beginner(self, beginner_features):
        result = _rules_classify_level(beginner_features)
        assert result.predicted_level == "beginner"

    def test_moderate_accuracy_returns_intermediate(self, intermediate_features):
        result = _rules_classify_level(intermediate_features)
        assert result.predicted_level == "intermediate"

    def test_high_accuracy_returns_advanced(self, advanced_features):
        result = _rules_classify_level(advanced_features)
        assert result.predicted_level == "advanced"

    def test_few_attempts_defaults_to_beginner(self):
        """Even with high accuracy, few attempts → beginner."""
        fv = FeatureVector(
            total_attempts=3,
            correct_attempts=3,
            accuracy=1.0,
            recent_accuracy=1.0,
        )
        result = _rules_classify_level(fv)
        assert result.predicted_level == "beginner"

    def test_probabilities_sum_to_one(self, intermediate_features):
        result = _rules_classify_level(intermediate_features)
        total = sum(result.probabilities.values())
        assert abs(total - 1.0) < 0.01

    def test_confidence_increases_with_attempts(self):
        fv_few = FeatureVector(total_attempts=3, correct_attempts=2, accuracy=0.67)
        fv_many = FeatureVector(total_attempts=50, correct_attempts=35, accuracy=0.7)
        r_few = _rules_classify_level(fv_few)
        r_many = _rules_classify_level(fv_many)
        assert r_many.confidence > r_few.confidence


class TestRulesDifficultyRecommendation:
    """Test rules-based difficulty recommendation."""

    def test_cold_start_recommends_easy(self, cold_start_features):
        result = _rules_recommend_difficulty(cold_start_features)
        assert result.recommended_difficulty == "easy"
        assert result.model_used == "rules"

    def test_beginner_gets_easy(self, beginner_features):
        result = _rules_recommend_difficulty(beginner_features)
        assert result.recommended_difficulty == "easy"

    def test_intermediate_gets_medium(self, intermediate_features):
        result = _rules_recommend_difficulty(intermediate_features)
        assert result.recommended_difficulty == "medium"

    def test_advanced_gets_hard(self, advanced_features):
        result = _rules_recommend_difficulty(advanced_features)
        assert result.recommended_difficulty == "hard"

    def test_improving_user_gets_harder(self):
        """Strong positive trend should nudge difficulty up."""
        fv = FeatureVector(
            total_attempts=20,
            correct_attempts=10,
            accuracy=0.5,
            recent_accuracy=0.8,
            accuracy_trend=0.3,
        )
        result = _rules_recommend_difficulty(fv)
        # Intermediate-level user with strong improvement → should get medium or hard
        assert result.recommended_difficulty in ("medium", "hard")

    def test_declining_user_gets_easier(self):
        """Strong negative trend should nudge difficulty down."""
        fv = FeatureVector(
            total_attempts=30,
            correct_attempts=22,
            accuracy=0.73,
            recent_accuracy=0.5,
            accuracy_trend=-0.23,
        )
        result = _rules_recommend_difficulty(fv)
        # Was intermediate but declining → should ease off
        assert result.recommended_difficulty in ("easy", "medium")


class TestRulesNextQuestion:
    """Test rules-based next question predictor."""

    def test_returns_all_candidate_difficulties(self, intermediate_features):
        result = _rules_next_question(
            intermediate_features, ["easy", "medium", "hard"]
        )
        assert "easy" in result.success_probabilities
        assert "medium" in result.success_probabilities
        assert "hard" in result.success_probabilities

    def test_easy_has_highest_success_prob(self, beginner_features):
        result = _rules_next_question(
            beginner_features, ["easy", "medium", "hard"]
        )
        assert result.success_probabilities["easy"] >= result.success_probabilities["hard"]

    def test_optimal_difficulty_targets_70_percent(self, intermediate_features):
        result = _rules_next_question(
            intermediate_features, ["easy", "medium", "hard"]
        )
        # Optimal should be the one closest to 70%
        probs = result.success_probabilities
        target = 0.7
        expected = min(probs.keys(), key=lambda d: abs(probs[d] - target))
        assert result.optimal_difficulty == expected

    def test_custom_candidates(self, intermediate_features):
        result = _rules_next_question(
            intermediate_features, ["easy", "hard"]
        )
        assert len(result.success_probabilities) == 2
        assert "medium" not in result.success_probabilities
