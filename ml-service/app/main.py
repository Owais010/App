"""
ML Service — FastAPI Application

Endpoints:
  POST /predict              — Generic predict (backward compat with mlService.js)
  POST /predict/level        — Predict user level for a topic
  POST /predict/difficulty   — Recommend next question difficulty
  POST /predict/next-question — Predict P(correct) per difficulty
  POST /predict/batch        — Batch predictions for multiple topics
  POST /features/{user_id}/{topic_id} — Get feature vector
  POST /cache/invalidate     — Invalidate feature cache
  GET  /health               — Health check
  GET  /metrics              — Prediction metrics
  POST /retrain/trigger      — Trigger model retraining
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.feature_engineering import (
    FeatureVector,
    get_features,
    get_features_batch,
    invalidate_cache,
)
from app.inference import (
    get_prediction_stats,
    predict_difficulty,
    predict_level,
    predict_next_question,
)
from app.metrics import get_metrics_summary, log_prediction_to_db, record_prediction
from app.model_loader import load_all_models, registry
from app.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    DifficultyRequest,
    DifficultyResponse,
    GenericPredictRequest,
    GenericPredictResponse,
    HealthResponse,
    LevelPredictionRequest,
    LevelPredictionResponse,
    NextQuestionRequest,
    NextQuestionResponse,
    TopicPrediction,
)
from app.security import verify_api_key

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# LIFESPAN — load models at startup
# ─────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup, cleanup on shutdown."""
    logger.info("Starting ML Service...")
    model_status = load_all_models()
    logger.info("Model load status: %s", model_status)
    yield
    logger.info("Shutting down ML Service...")


# ─────────────────────────────────────────────────────────────────────────────
# APP CREATION
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Quiz ML Service",
    description="Adaptive quiz intelligence — level classification, difficulty recommendation, and learning analytics",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  GENERIC PREDICT (backward compat)                                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


@app.post("/predict", response_model=GenericPredictResponse)
async def generic_predict(
    req: GenericPredictRequest,
    _: str = Depends(verify_api_key),
):
    """
    Generic prediction endpoint — matches the existing mlService.js client.

    Dispatches to the appropriate prediction function based on `prediction_type`.
    """
    t0 = time.time()

    if not req.user_id or not req.topic_id:
        raise HTTPException(400, "user_id and topic_id are required")

    precomputed = (
        FeatureVector(**req.features) if req.features else None
    )

    if req.prediction_type == "level":
        result = await predict_level(req.user_id, req.topic_id, precomputed)
        prediction = {
            "level": result.predicted_level,
            "probabilities": result.probabilities,
        }
        confidence = result.confidence
        model_used = result.model_used

    elif req.prediction_type == "difficulty":
        result = await predict_difficulty(
            req.user_id, req.topic_id, precomputed
        )
        prediction = {
            "difficulty": result.recommended_difficulty,
            "success_prob": result.predicted_success_prob,
            "difficulty_probs": result.difficulty_probs,
        }
        confidence = result.confidence
        model_used = result.model_used

    elif req.prediction_type == "next_question":
        result = await predict_next_question(
            req.user_id, req.topic_id, precomputed_features=precomputed
        )
        prediction = {
            "success_probabilities": result.success_probabilities,
            "optimal_difficulty": result.optimal_difficulty,
        }
        confidence = result.confidence
        model_used = result.model_used

    else:
        raise HTTPException(
            400,
            f"Unknown prediction_type: {req.prediction_type}. "
            "Use: level, difficulty, next_question",
        )

    latency_ms = (time.time() - t0) * 1000
    record_prediction(req.prediction_type, model_used, latency_ms)

    return GenericPredictResponse(
        prediction=prediction,
        model_used=model_used,
        confidence=confidence,
    )


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  TYPED ENDPOINTS                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


@app.post("/predict/level", response_model=LevelPredictionResponse)
async def predict_level_endpoint(
    req: LevelPredictionRequest,
    _: str = Depends(verify_api_key),
):
    """Predict user level (beginner/intermediate/advanced) for a topic."""
    t0 = time.time()
    result = await predict_level(req.user_id, req.topic_id, req.features)
    latency_ms = (time.time() - t0) * 1000
    record_prediction("level", result.model_used, latency_ms)

    # Log to DB (non-blocking)
    await log_prediction_to_db(
        user_id=req.user_id,
        topic_id=req.topic_id,
        model_name="level_classifier",
        model_version=result.model_used,
        predicted_level=result.predicted_level,
        confidence=result.confidence,
        feature_snapshot=result.features_used.model_dump() if result.features_used else None,
    )

    return result


@app.post("/predict/difficulty", response_model=DifficultyResponse)
async def predict_difficulty_endpoint(
    req: DifficultyRequest,
    _: str = Depends(verify_api_key),
):
    """Recommend next question difficulty for a topic."""
    t0 = time.time()
    result = await predict_difficulty(req.user_id, req.topic_id, req.features)
    latency_ms = (time.time() - t0) * 1000
    record_prediction("difficulty", result.model_used, latency_ms)
    return result


@app.post("/predict/next-question", response_model=NextQuestionResponse)
async def predict_next_question_endpoint(
    req: NextQuestionRequest,
    _: str = Depends(verify_api_key),
):
    """Predict P(correct) for each candidate difficulty."""
    t0 = time.time()
    result = await predict_next_question(
        req.user_id,
        req.topic_id,
        req.candidate_difficulties,
        req.features,
    )
    latency_ms = (time.time() - t0) * 1000
    record_prediction("next_question", result.model_used, latency_ms)
    return result


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_endpoint(
    req: BatchPredictionRequest,
    _: str = Depends(verify_api_key),
):
    """Batch predictions for multiple topics."""
    t0 = time.time()

    feature_map = await get_features_batch(req.user_id, req.topic_ids)
    predictions = []

    for tid in req.topic_ids:
        fv = feature_map.get(tid)
        level_result = await predict_level(req.user_id, tid, fv)
        diff_result = await predict_difficulty(req.user_id, tid, fv)

        predictions.append(
            TopicPrediction(
                topic_id=tid,
                predicted_level=level_result.predicted_level,
                confidence=level_result.confidence,
                recommended_difficulty=diff_result.recommended_difficulty,
                predicted_success_prob=diff_result.predicted_success_prob,
            )
        )

    latency_ms = (time.time() - t0) * 1000
    model_used = predictions[0].predicted_level if predictions else "rules"

    return BatchPredictionResponse(
        predictions=predictions,
        model_used="batch",
    )


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FEATURE ENDPOINTS                                                      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


@app.get("/features/{user_id}/{topic_id}")
async def get_features_endpoint(
    user_id: str,
    topic_id: str,
    _: str = Depends(verify_api_key),
):
    """Get computed feature vector for a user-topic pair."""
    fv = await get_features(user_id, topic_id)
    return fv.model_dump()


@app.post("/cache/invalidate")
async def invalidate_cache_endpoint(
    user_id: str,
    topic_id: str | None = None,
    _: str = Depends(verify_api_key),
):
    """Invalidate feature cache after new answers."""
    invalidate_cache(user_id, topic_id)
    return {"status": "ok", "invalidated": f"{user_id}/{topic_id or '*'}"}


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  HEALTH & MONITORING                                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check — no auth required."""
    return HealthResponse(
        status="healthy",
        models_loaded=registry.list_models(),
        version="1.0.0",
    )


@app.get("/metrics")
async def metrics_endpoint(_: str = Depends(verify_api_key)):
    """Prediction metrics — counts, latencies, accuracy."""
    return {
        "prediction_stats": get_prediction_stats(),
        "detailed_metrics": get_metrics_summary(),
        "models": registry.list_models(),
    }


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  RETRAINING TRIGGER                                                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝


@app.post("/retrain/trigger")
async def trigger_retrain(
    model_name: str = "all",
    _: str = Depends(verify_api_key),
):
    """
    Trigger model retraining.

    In production this would enqueue a training job.
    For now it returns instructions.
    """
    return {
        "status": "accepted",
        "message": f"Retraining '{model_name}' queued. "
        "Run `python -m training.train_all` to retrain locally.",
        "model_name": model_name,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL,
    )
