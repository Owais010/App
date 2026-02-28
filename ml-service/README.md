# Adaptive Learning Intelligence Engine

A stateless Machine Learning microservice for educational adaptive learning systems.

## Overview

This microservice provides machine learning predictions for:

- **Skill Gap Estimation** (Regression) - Identifies learning gaps
- **Difficulty Suitability Prediction** (Classification) - Recommends content difficulty
- **Topic Recommendation Ranking** (Scoring) - Ranks content by engagement potential
- **Adaptation Signals** - Provides actionable learning path adjustments

## Architecture

```
ml-service/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── schemas.py              # Pydantic models
│   ├── inference.py            # Prediction logic
│   ├── feature_engineering.py  # Feature derivation
│   ├── model_loader.py         # Model management
│   └── config.py               # Configuration
├── models/                     # Trained model files
│   ├── skill_gap_model.pkl
│   ├── difficulty_model.pkl
│   └── ranking_model.pkl
├── training/                   # Training scripts
│   ├── generate_data.py
│   ├── train_skill_gap.py
│   ├── train_difficulty.py
│   ├── train_ranking.py
│   └── train_all.py
├── examples/                   # Integration examples
│   └── nodejs_client.js
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Quick Start

### 1. Install Dependencies

```bash
cd ml-service
pip install -r requirements.txt
```

### 2. Train Models

```bash
python training/train_all.py
```

This will:

- Generate synthetic training data (5000 samples)
- Train all three models
- Save models to `models/` directory

### 3. Start the Service

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
curl http://localhost:8000/health
```

## API Endpoints

### POST /predict

Generate predictions for a learner-topic pair.

**Request:**

```json
{
  "user_id": "user_12345",
  "topic_id": "topic_001",
  "attempt_count": 15,
  "correct_attempts": 9,
  "avg_response_time": 45.5,
  "self_confidence_rating": 0.65,
  "difficulty_feedback": 3,
  "session_duration": 25.0,
  "previous_mastery_score": 0.55,
  "time_since_last_attempt": 24.0
}
```

**Response:**

```json
{
  "skill_gap": {
    "gap_score": 0.4523,
    "weak": false
  },
  "difficulty": {
    "difficulty_level": "medium"
  },
  "ranking": {
    "ranking_score": 0.5821
  },
  "adaptation": {
    "action": "continue_current_path"
  },
  "request_id": "abc123...",
  "prediction_time_ms": 15.23
}
```

### GET /health

Check service health status.

**Response:**

```json
{
  "status": "healthy",
  "models_loaded": true,
  "version": "1.0.0"
}
```

## Docker Deployment

### Build and Run

```bash
docker build -t adaptive-learning-engine .
docker run -p 8000:8000 adaptive-learning-engine
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Node.js Integration

```javascript
const axios = require("axios");

const mlClient = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 5000,
});

async function getPrediction(learnerData) {
  const response = await mlClient.post("/predict", learnerData);
  return response.data;
}

// Example usage
const prediction = await getPrediction({
  user_id: "user_123",
  topic_id: "topic_001",
  attempt_count: 10,
  correct_attempts: 7,
  avg_response_time: 30.0,
  self_confidence_rating: 0.7,
  difficulty_feedback: 3,
  session_duration: 20.0,
  previous_mastery_score: 0.6,
  time_since_last_attempt: 48.0,
});

console.log(prediction.adaptation.action);
// Output: "continue_current_path"
```

See `examples/nodejs_client.js` for a complete integration example.

## Models

### Skill Gap Model

- **Algorithm:** GradientBoostingRegressor
- **Output:** `gap_score` (0-1), `weak` (boolean)
- **Threshold:** weak = true if gap_score > 0.6

### Difficulty Model

- **Algorithm:** RandomForestClassifier
- **Output:** "easy", "medium", or "hard"
- **Labels:** Based on accuracy rate thresholds

### Ranking Model

- **Algorithm:** GradientBoostingRegressor
- **Output:** `ranking_score` for content prioritization

## Adaptation Rules

| Condition                                 | Action                   |
| ----------------------------------------- | ------------------------ |
| gap_score > 0.75                          | add_foundation_resources |
| difficulty == hard AND failure_rate > 0.6 | reduce_difficulty        |
| accuracy_rate > 0.85                      | increase_difficulty      |
| Default                                   | continue_current_path    |

## Feature Engineering

The service computes the following derived features:

| Feature                    | Formula                                   |
| -------------------------- | ----------------------------------------- |
| accuracy_rate              | correct_attempts / attempt_count          |
| failure_rate               | 1 - accuracy_rate                         |
| learning_velocity          | previous_mastery_score / session_duration |
| confidence_performance_gap | self_confidence_rating - accuracy_rate    |
| difficulty_stress_index    | difficulty_feedback × failure_rate        |
| persistence_score          | session_duration / (attempt_count + 1)    |

## Configuration

Environment variables:

| Variable     | Default | Description          |
| ------------ | ------- | -------------------- |
| LOG_LEVEL    | INFO    | Logging level        |
| CORS_ORIGINS | \*      | Allowed CORS origins |

## Development

### Run Tests

```bash
pytest tests/
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License
