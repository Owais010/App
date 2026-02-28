"""
Configuration module for the Adaptive Learning Intelligence Engine.

Contains all configuration settings, paths, and constants used across the service.
"""

import os
from pathlib import Path


# Base directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

# Model file paths
SKILL_GAP_MODEL_PATH = MODELS_DIR / "skill_gap_model.pkl"
DIFFICULTY_MODEL_PATH = MODELS_DIR / "difficulty_model.pkl"
RANKING_MODEL_PATH = MODELS_DIR / "ranking_model.pkl"

# API Configuration
API_TITLE = "Adaptive Learning Intelligence Engine"
API_DESCRIPTION = """
Machine Learning Microservice for educational adaptive learning.

Provides:
- Skill Gap Estimation (Regression)
- Difficulty Suitability Prediction (Classification)
- Topic Recommendation Ranking (Scoring)
- Adaptation Signals
"""
API_VERSION = "1.0.0"

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Model Thresholds
SKILL_GAP_WEAK_THRESHOLD = 0.6
ADAPTATION_GAP_HIGH_THRESHOLD = 0.75
ADAPTATION_ACCURACY_HIGH_THRESHOLD = 0.85
ADAPTATION_FAILURE_HIGH_THRESHOLD = 0.6

# Difficulty Labels
DIFFICULTY_LABELS = {
    0: "easy",
    1: "medium",
    2: "hard"
}
