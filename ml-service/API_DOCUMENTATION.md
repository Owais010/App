# Adaptive Learning Intelligence Engine

## Overview

The **Adaptive Learning Intelligence Engine** is a machine learning microservice designed to personalize educational experiences. It analyzes a learner's interaction data and provides intelligent recommendations to optimize their learning path.

### What This Service Does

When a learner interacts with educational content (attempting questions, completing exercises, spending time on topics), this service:

1. **Estimates Skill Gaps** - Identifies how much the learner is struggling with a topic
2. **Predicts Appropriate Difficulty** - Determines if content is too easy, appropriate, or too hard
3. **Ranks Topic Priority** - Scores how urgently a topic needs attention
4. **Recommends Actions** - Suggests what the learning platform should do next

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ADAPTIVE LEARNING ENGINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                                                           │
│   │   Learner   │                                                           │
│   │ Interaction │──────────┐                                                │
│   │    Data     │          │                                                │
│   └─────────────┘          ▼                                                │
│                    ┌───────────────┐                                        │
│                    │   Feature     │                                        │
│                    │  Engineering  │                                        │
│                    │               │                                        │
│                    │ • Accuracy    │                                        │
│                    │ • Persistence │                                        │
│                    │ • Confidence  │                                        │
│                    └───────┬───────┘                                        │
│                            │                                                │
│              ┌─────────────┼─────────────┐                                  │
│              ▼             ▼             ▼                                  │
│      ┌──────────────┐ ┌──────────┐ ┌──────────────┐                         │
│      │  Skill Gap   │ │Difficulty│ │   Ranking    │                         │
│      │    Model     │ │  Model   │ │    Model     │                         │
│      │ (Regression) │ │ (Class.) │ │ (Regression) │                         │
│      └──────┬───────┘ └────┬─────┘ └──────┬───────┘                         │
│             │              │              │                                 │
│             └──────────────┼──────────────┘                                 │
│                            ▼                                                │
│                    ┌───────────────┐                                        │
│                    │  Adaptation   │                                        │
│                    │    Engine     │                                        │
│                    └───────┬───────┘                                        │
│                            │                                                │
│                            ▼                                                │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    PERSONALIZED RECOMMENDATIONS                      │   │
│   │  • Gap Score  • Difficulty Level  • Priority Rank  • Next Action    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Get learning recommendations |
| `/health` | GET | Check service status |
| `/metrics` | GET | Prometheus metrics |

---

## Making a Prediction Request

### Endpoint
```
POST /predict
```

### Request Format

Send a JSON object with the learner's interaction data:

```json
{
  "user_id": "learner-12345",
  "topic_id": "algebra-quadratic-equations",
  "attempt_count": 15,
  "correct_attempts": 9,
  "avg_response_time": 25.5,
  "self_confidence_rating": 0.6,
  "difficulty_feedback": 4,
  "session_duration": 45.0,
  "previous_mastery_score": 0.55,
  "time_since_last_attempt": 48.0
}
```

### Input Fields Explained

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `user_id` | string | any | Unique identifier for the learner |
| `topic_id` | string | any | Unique identifier for the learning topic |
| `attempt_count` | integer | ≥ 0 | Total number of attempts on this topic |
| `correct_attempts` | integer | ≥ 0 | Number of successful/correct attempts |
| `avg_response_time` | float | ≥ 0 | Average time (seconds) to answer questions |
| `self_confidence_rating` | float | 0.0 - 1.0 | Learner's self-reported confidence (0=not confident, 1=very confident) |
| `difficulty_feedback` | integer | 1 - 5 | Learner's perception of difficulty (1=very easy, 5=very hard) |
| `session_duration` | float | ≥ 0 | Total time (minutes) spent in current session |
| `previous_mastery_score` | float | 0.0 - 1.0 | Prior mastery level of this topic (0=none, 1=complete mastery) |
| `time_since_last_attempt` | float | ≥ 0 | Hours since last interaction with this topic |

### Response Format

```json
{
  "skill_gap": {
    "gap_score": 0.35,
    "weak": false
  },
  "difficulty": {
    "difficulty_level": "medium"
  },
  "ranking": {
    "ranking_score": 0.72
  },
  "adaptation": {
    "action": "continue_current_path"
  },
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "prediction_time_ms": 12.5
}
```

### Output Fields Explained

#### Skill Gap Assessment
| Field | Type | Description |
|-------|------|-------------|
| `gap_score` | float (0-1) | How much the learner is struggling. **0** = no gap (mastered), **1** = severe gap (struggling significantly) |
| `weak` | boolean | `true` if gap_score > 0.5, indicating the learner needs additional support |

**Interpretation:**
- **0.0 - 0.2**: Excellent understanding, learner is performing well
- **0.2 - 0.4**: Good progress, minor areas for improvement
- **0.4 - 0.6**: Moderate struggle, may need some help
- **0.6 - 0.8**: Significant difficulty, intervention recommended
- **0.8 - 1.0**: Critical gap, urgent support needed

#### Difficulty Assessment
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `difficulty_level` | string | `"easy"`, `"medium"`, `"hard"` | How appropriate the current content difficulty is for this learner |

**Interpretation:**
- **easy**: Content is too simple; learner may be bored or under-challenged
- **medium**: Content difficulty is appropriate for the learner
- **hard**: Content is challenging; learner may need easier material first

#### Topic Ranking
| Field | Type | Description |
|-------|------|-------------|
| `ranking_score` | float (0-1) | Priority score for this topic. **Higher = more important** to focus on |

**Interpretation:**
- **0.0 - 0.3**: Low priority - learner is doing well, topic can wait
- **0.3 - 0.6**: Medium priority - topic needs attention but not urgent
- **0.6 - 0.8**: High priority - recommend focusing on this topic soon
- **0.8 - 1.0**: Critical priority - immediate attention needed

#### Adaptation Action
| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `action` | string | See below | Recommended action for the learning platform |

**Possible Actions:**

| Action | Meaning | When Triggered |
|--------|---------|----------------|
| `add_foundation_resources` | Provide remedial/prerequisite content | Skill gap > 75% |
| `reduce_difficulty` | Move to easier content | Hard content + failure rate > 60% |
| `increase_difficulty` | Move to harder content | Accuracy > 85% |
| `continue_current_path` | Maintain current learning path | Performance is appropriate |

---

## Example Use Cases

### Example 1: Struggling Learner

**Input:**
```json
{
  "user_id": "student-001",
  "topic_id": "calculus-derivatives",
  "attempt_count": 20,
  "correct_attempts": 5,
  "avg_response_time": 120.0,
  "self_confidence_rating": 0.2,
  "difficulty_feedback": 5,
  "session_duration": 60.0,
  "previous_mastery_score": 0.3,
  "time_since_last_attempt": 168.0
}
```

**Response:**
```json
{
  "skill_gap": {
    "gap_score": 0.82,
    "weak": true
  },
  "difficulty": {
    "difficulty_level": "hard"
  },
  "ranking": {
    "ranking_score": 0.25
  },
  "adaptation": {
    "action": "add_foundation_resources"
  }
}
```

**Interpretation:** This learner is struggling significantly (82% gap). They've only answered 25% correctly, feel unconfident, and perceive the material as very hard. The system recommends adding foundational resources to build prerequisite knowledge.

---

### Example 2: High-Performing Learner

**Input:**
```json
{
  "user_id": "student-002",
  "topic_id": "algebra-linear-equations",
  "attempt_count": 30,
  "correct_attempts": 28,
  "avg_response_time": 8.0,
  "self_confidence_rating": 0.9,
  "difficulty_feedback": 1,
  "session_duration": 25.0,
  "previous_mastery_score": 0.85,
  "time_since_last_attempt": 2.0
}
```

**Response:**
```json
{
  "skill_gap": {
    "gap_score": 0.08,
    "weak": false
  },
  "difficulty": {
    "difficulty_level": "easy"
  },
  "ranking": {
    "ranking_score": 0.91
  },
  "adaptation": {
    "action": "increase_difficulty"
  }
}
```

**Interpretation:** This learner has mastered the topic (93% accuracy, 8% gap). The content feels easy to them. The system recommends increasing difficulty to keep them challenged and engaged.

---

### Example 3: Average Learner

**Input:**
```json
{
  "user_id": "student-003",
  "topic_id": "geometry-triangles",
  "attempt_count": 15,
  "correct_attempts": 10,
  "avg_response_time": 35.0,
  "self_confidence_rating": 0.6,
  "difficulty_feedback": 3,
  "session_duration": 40.0,
  "previous_mastery_score": 0.6,
  "time_since_last_attempt": 24.0
}
```

**Response:**
```json
{
  "skill_gap": {
    "gap_score": 0.32,
    "weak": false
  },
  "difficulty": {
    "difficulty_level": "medium"
  },
  "ranking": {
    "ranking_score": 0.68
  },
  "adaptation": {
    "action": "continue_current_path"
  }
}
```

**Interpretation:** This learner is progressing normally (67% accuracy, 32% gap). The difficulty feels appropriate. The system recommends continuing the current learning path.

---

## Integration Examples

### cURL
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "learner-123",
    "topic_id": "math-fractions",
    "attempt_count": 10,
    "correct_attempts": 7,
    "avg_response_time": 15.0,
    "self_confidence_rating": 0.7,
    "difficulty_feedback": 3,
    "session_duration": 30.0,
    "previous_mastery_score": 0.5,
    "time_since_last_attempt": 12.0
  }'
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/predict",
    json={
        "user_id": "learner-123",
        "topic_id": "math-fractions",
        "attempt_count": 10,
        "correct_attempts": 7,
        "avg_response_time": 15.0,
        "self_confidence_rating": 0.7,
        "difficulty_feedback": 3,
        "session_duration": 30.0,
        "previous_mastery_score": 0.5,
        "time_since_last_attempt": 12.0
    }
)

result = response.json()
print(f"Skill Gap: {result['skill_gap']['gap_score']:.0%}")
print(f"Difficulty: {result['difficulty']['difficulty_level']}")
print(f"Action: {result['adaptation']['action']}")
```

### Node.js
```javascript
const axios = require('axios');

async function getPrediction(learnerData) {
  const response = await axios.post('http://localhost:8000/predict', {
    user_id: learnerData.userId,
    topic_id: learnerData.topicId,
    attempt_count: learnerData.attempts,
    correct_attempts: learnerData.correct,
    avg_response_time: learnerData.avgTime,
    self_confidence_rating: learnerData.confidence,
    difficulty_feedback: learnerData.difficultyRating,
    session_duration: learnerData.duration,
    previous_mastery_score: learnerData.mastery,
    time_since_last_attempt: learnerData.hoursSinceLast
  });

  return {
    gapScore: response.data.skill_gap.gap_score,
    difficulty: response.data.difficulty.difficulty_level,
    priority: response.data.ranking.ranking_score,
    recommendedAction: response.data.adaptation.action
  };
}
```

---

## Health Check

### Endpoint
```
GET /health
```

### Response
```json
{
  "status": "healthy",
  "models_loaded": true,
  "version": "1.0.0"
}
```

| Field | Description |
|-------|-------------|
| `status` | Service health status (`"healthy"` or `"degraded"`) |
| `models_loaded` | Whether ML models are loaded and ready |
| `version` | API version |

---

## Error Responses

### Validation Error (422)
When input data is invalid:
```json
{
  "detail": [
    {
      "loc": ["body", "self_confidence_rating"],
      "msg": "ensure this value is less than or equal to 1",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### Service Unavailable (503)
When models are not loaded:
```json
{
  "error": "ServiceUnavailable",
  "detail": "Models are not loaded. Please ensure training has been completed."
}
```

---

## Security (Optional)

### API Key Authentication
If `API_KEY` environment variable is set, requests must include:
```
X-API-Key: your-api-key-here
```

### Rate Limiting
Default: 100 requests per 60 seconds per client.

Configure via environment variables:
- `RATE_LIMIT_REQUESTS`: Max requests per window (default: 100)
- `RATE_LIMIT_WINDOW`: Window size in seconds (default: 60)

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
```

---

## Summary

This service transforms raw learner interaction data into actionable insights:

| Input | Output |
|-------|--------|
| Attempt counts, response times, confidence ratings | Skill gap score (0-1) |
| Historical performance, session duration | Recommended difficulty level |
| Learning patterns, mastery progression | Topic priority ranking |
| All of the above | Specific action to take |

**Use this service to:**
- Personalize content difficulty in real-time
- Identify struggling learners early
- Prioritize which topics need immediate attention
- Automate adaptive learning decisions

---

## Quick Start

```bash
# 1. Start the service
cd ml-service
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Check health
curl http://localhost:8000/health

# 3. Make predictions
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","topic_id":"test","attempt_count":10,"correct_attempts":7,"avg_response_time":20,"self_confidence_rating":0.7,"difficulty_feedback":3,"session_duration":30,"previous_mastery_score":0.5,"time_since_last_attempt":24}'
```
