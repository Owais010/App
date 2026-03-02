"""
Pytest fixtures for ML service tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import FeatureVector


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """Default test API key."""
    return "default_test_key"


@pytest.fixture
def auth_headers(api_key):
    """Headers with API key."""
    return {"X-API-Key": api_key, "Content-Type": "application/json"}


@pytest.fixture
def beginner_features():
    """Feature vector for a beginner user."""
    return FeatureVector(
        total_attempts=8,
        correct_attempts=2,
        accuracy=0.25,
        weighted_score=1.5,
        recent_accuracy=0.3,
        accuracy_trend=0.05,
        streak_length=1,
        avg_time_per_q=30.0,
        days_since_last=5.0,
        easy_accuracy=0.4,
        medium_accuracy=0.2,
        hard_accuracy=0.0,
        global_accuracy=0.28,
        topics_attempted=2,
    )


@pytest.fixture
def intermediate_features():
    """Feature vector for an intermediate user."""
    return FeatureVector(
        total_attempts=30,
        correct_attempts=19,
        accuracy=0.63,
        weighted_score=8.0,
        recent_accuracy=0.7,
        accuracy_trend=0.07,
        streak_length=4,
        avg_time_per_q=15.0,
        days_since_last=2.0,
        easy_accuracy=0.85,
        medium_accuracy=0.6,
        hard_accuracy=0.3,
        global_accuracy=0.58,
        topics_attempted=8,
    )


@pytest.fixture
def advanced_features():
    """Feature vector for an advanced user."""
    return FeatureVector(
        total_attempts=80,
        correct_attempts=68,
        accuracy=0.85,
        weighted_score=25.0,
        recent_accuracy=0.9,
        accuracy_trend=0.05,
        streak_length=10,
        avg_time_per_q=8.0,
        days_since_last=1.0,
        easy_accuracy=0.95,
        medium_accuracy=0.88,
        hard_accuracy=0.7,
        global_accuracy=0.82,
        topics_attempted=15,
    )


@pytest.fixture
def cold_start_features():
    """Feature vector for a brand new user (cold start)."""
    return FeatureVector(
        total_attempts=0,
        correct_attempts=0,
        accuracy=0.0,
        weighted_score=0.0,
        recent_accuracy=0.0,
        accuracy_trend=0.0,
        streak_length=0,
        avg_time_per_q=0.0,
        days_since_last=-1.0,
        easy_accuracy=0.0,
        medium_accuracy=0.0,
        hard_accuracy=0.0,
        global_accuracy=0.0,
        topics_attempted=0,
    )
