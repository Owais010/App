"""Integration tests for FastAPI endpoints."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_payload():
    """Create valid request payload."""
    return {
        "user_id": "test-learner-123",
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


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    def test_health_returns_ok(self, client):
        """Test health endpoint returns status ok."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "models_loaded" in data


class TestPredictEndpoint:
    """Tests for /predict endpoint - requires models loaded."""
    
    @pytest.mark.skip(reason="Requires models to be loaded in test environment")
    def test_predict_valid_input(self, client, valid_payload):
        """Test prediction with valid input."""
        pass
    
    def test_predict_missing_field(self, client, valid_payload):
        """Test prediction with missing required field."""
        del valid_payload["attempt_count"]
        
        response = client.post("/predict", json=valid_payload)
        
        assert response.status_code == 422
    
    def test_predict_invalid_type(self, client, valid_payload):
        """Test prediction with invalid data type."""
        valid_payload["attempt_count"] = "not-a-number"
        
        response = client.post("/predict", json=valid_payload)
        
        assert response.status_code == 422
    
    def test_predict_negative_value(self, client, valid_payload):
        """Test prediction with negative value where positive required."""
        valid_payload["attempt_count"] = -5
        
        response = client.post("/predict", json=valid_payload)
        
        assert response.status_code == 422
    
    def test_predict_out_of_range_confidence(self, client, valid_payload):
        """Test with confidence rating out of [0,1] range."""
        valid_payload["self_confidence_rating"] = 1.5
        
        response = client.post("/predict", json=valid_payload)
        
        assert response.status_code == 422


class TestInputValidation:
    """Tests for input validation."""
    
    def test_difficulty_feedback_range(self, client, valid_payload):
        """Test difficulty_feedback validation."""
        valid_payload["difficulty_feedback"] = 0
        response = client.post("/predict", json=valid_payload)
        assert response.status_code == 422
        
        valid_payload["difficulty_feedback"] = 6
        response = client.post("/predict", json=valid_payload)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
