"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test the /health endpoint (no auth required)."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "models_loaded" in data

    def test_health_includes_version(self, client):
        resp = client.get("/health")
        assert resp.json()["version"] == "1.0.0"


class TestAuthSecurity:
    """Test API key authentication."""

    def test_missing_api_key_returns_401(self, client):
        resp = client.post("/predict", json={
            "user_id": "u1",
            "topic_id": "t1",
            "prediction_type": "level",
        })
        assert resp.status_code == 401

    def test_wrong_api_key_returns_403(self, client):
        resp = client.post(
            "/predict",
            json={"user_id": "u1", "topic_id": "t1", "prediction_type": "level"},
            headers={"X-API-Key": "wrong_key"},
        )
        assert resp.status_code == 403

    def test_valid_api_key_passes(self, client, auth_headers):
        resp = client.post(
            "/predict",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "prediction_type": "level",
                "features": {
                    "total_attempts": 10,
                    "correct_attempts": 6,
                    "accuracy": 0.6,
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestGenericPredictEndpoint:
    """Test the /predict endpoint (backward compat)."""

    def test_level_prediction(self, client, auth_headers):
        resp = client.post(
            "/predict",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "prediction_type": "level",
                "features": {
                    "total_attempts": 20,
                    "correct_attempts": 15,
                    "accuracy": 0.75,
                    "weighted_score": 10.0,
                    "recent_accuracy": 0.8,
                    "accuracy_trend": 0.05,
                    "streak_length": 5,
                    "avg_time_per_q": 12.0,
                    "days_since_last": 2.0,
                    "easy_accuracy": 0.9,
                    "medium_accuracy": 0.75,
                    "hard_accuracy": 0.5,
                    "global_accuracy": 0.7,
                    "topics_attempted": 8,
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "prediction" in data
        assert "level" in data["prediction"]
        assert data["model_used"] == "rules"

    def test_difficulty_prediction(self, client, auth_headers):
        resp = client.post(
            "/predict",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "prediction_type": "difficulty",
                "features": {
                    "total_attempts": 5,
                    "correct_attempts": 2,
                    "accuracy": 0.4,
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "difficulty" in data["prediction"]

    def test_unknown_type_returns_400(self, client, auth_headers):
        resp = client.post(
            "/predict",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "prediction_type": "unknown",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_missing_user_id_returns_400(self, client, auth_headers):
        resp = client.post(
            "/predict",
            json={"prediction_type": "level"},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestTypedEndpoints:
    """Test typed prediction endpoints."""

    def test_predict_level(self, client, auth_headers):
        resp = client.post(
            "/predict/level",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "features": {
                    "total_attempts": 50,
                    "correct_attempts": 42,
                    "accuracy": 0.84,
                    "recent_accuracy": 0.9,
                    "easy_accuracy": 0.95,
                    "medium_accuracy": 0.85,
                    "hard_accuracy": 0.7,
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["predicted_level"] == "advanced"
        assert "probabilities" in data

    def test_predict_difficulty(self, client, auth_headers):
        resp = client.post(
            "/predict/difficulty",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "features": {
                    "total_attempts": 10,
                    "correct_attempts": 6,
                    "accuracy": 0.6,
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommended_difficulty"] in ("easy", "medium", "hard")

    def test_predict_next_question(self, client, auth_headers):
        resp = client.post(
            "/predict/next-question",
            json={
                "user_id": "u1",
                "topic_id": "t1",
                "candidate_difficulties": ["easy", "medium", "hard"],
                "features": {
                    "total_attempts": 25,
                    "correct_attempts": 15,
                    "accuracy": 0.6,
                    "easy_accuracy": 0.8,
                    "medium_accuracy": 0.6,
                    "hard_accuracy": 0.3,
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success_probabilities" in data
        assert "optimal_difficulty" in data

    def test_predict_batch(self, client, auth_headers):
        resp = client.post(
            "/predict/batch",
            json={
                "user_id": "u1",
                "topic_ids": ["t1", "t2"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["predictions"]) == 2


class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    def test_metrics_requires_auth(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 401

    def test_metrics_returns_structure(self, client, auth_headers):
        resp = client.get("/metrics", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "prediction_stats" in data
        assert "models" in data
