"""
Adaptive Learning Intelligence Engine - Main FastAPI Application

A stateless Machine Learning microservice for educational adaptive learning.
Provides prediction endpoints for skill gap estimation, difficulty classification,
topic ranking, and adaptation signals.

Production Features:
- API Key Authentication (via X-API-Key header)
- Rate Limiting (configurable via environment)
- Prometheus Metrics (/metrics endpoint)
- Request tracking with unique IDs
- Graceful shutdown handling
"""

import logging
import time
import uuid
import signal
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import (
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    LOG_LEVEL,
    LOG_FORMAT
)
from app.schemas import (
    PredictionInput,
    PredictionResponse,
    SkillGapOutput,
    DifficultyOutput,
    RankingOutput,
    AdaptationOutput,
    HealthResponse,
    ErrorResponse
)
from app.inference import run_inference
from app.model_loader import get_model_loader
from app.security import SecurityMiddleware, rate_limiter
from app.metrics import MetricsMiddleware, metrics_endpoint


# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.
    
    Loads models on startup and performs cleanup on shutdown.
    Handles graceful shutdown with proper resource cleanup.
    """
    # Startup: Load all models
    logger.info("Starting Adaptive Learning Intelligence Engine...")
    model_loader = get_model_loader()
    
    try:
        success = model_loader.load_all_models()
        if success:
            logger.info("All models loaded successfully")
        else:
            logger.warning("Failed to load some models - service may not function correctly")
    except FileNotFoundError as e:
        logger.warning(f"Models not found - run training scripts first: {e}")
    except Exception as e:
        logger.error(f"Error loading models: {e}")
    
    # Background task for rate limiter cleanup
    cleanup_task = asyncio.create_task(_rate_limiter_cleanup())
    
    yield
    
    # Shutdown: Cleanup
    logger.info("Shutting down Adaptive Learning Intelligence Engine...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete")


async def _rate_limiter_cleanup():
    """Periodic cleanup of rate limiter state."""
    while True:
        await asyncio.sleep(60)  # Every minute
        rate_limiter.cleanup()


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS for Node.js backend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS
)

# Add security middleware (API key auth + rate limiting)
app.add_middleware(SecurityMiddleware)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Add Prometheus metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Middleware to add request ID and timing to all requests.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    process_time = (time.perf_counter() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    
    logger.info(f"Request {request_id} completed in {process_time:.2f}ms")
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Request {request_id} failed with error: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred",
            "request_id": request_id
        }
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        500: {"model": ErrorResponse, "description": "Server error"},
        503: {"model": ErrorResponse, "description": "Models not loaded"}
    },
    summary="Generate Predictions",
    description="Generate skill gap, difficulty, ranking, and adaptation predictions for a learner-topic pair."
)
async def predict(request: Request, input_data: PredictionInput) -> PredictionResponse:
    """
    Main prediction endpoint.
    
    Performs:
    - Skill Gap Estimation (Regression)
    - Difficulty Suitability Prediction (Classification)
    - Topic Recommendation Ranking (Scoring)
    - Adaptation Signal Generation
    
    Args:
        request: FastAPI request object.
        input_data: Validated prediction input data.
        
    Returns:
        PredictionResponse containing all prediction results.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.perf_counter()
    
    logger.info(f"Request {request_id}: Processing prediction for user={input_data.user_id}, "
                f"topic={input_data.topic_id}")
    
    # Check if models are loaded
    model_loader = get_model_loader()
    if not model_loader.is_loaded:
        logger.error(f"Request {request_id}: Models not loaded")
        raise HTTPException(
            status_code=503,
            detail="Models are not loaded. Please ensure training has been completed."
        )
    
    try:
        # Convert Pydantic model to dict for processing
        input_dict = input_data.model_dump()
        
        # Run inference
        result = run_inference(input_dict)
        
        # Calculate prediction time
        prediction_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Build response
        response = PredictionResponse(
            skill_gap=SkillGapOutput(**result["skill_gap"]),
            difficulty=DifficultyOutput(**result["difficulty"]),
            ranking=RankingOutput(**result["ranking"]),
            adaptation=AdaptationOutput(**result["adaptation"]),
            request_id=request_id,
            prediction_time_ms=round(prediction_time_ms, 2)
        )
        
        logger.info(f"Request {request_id}: Prediction completed in {prediction_time_ms:.2f}ms")
        
        return response
        
    except ValueError as e:
        logger.error(f"Request {request_id}: Validation error - {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Request {request_id}: Prediction failed - {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction failed")


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and model loading status."
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with service status information.
    """
    model_loader = get_model_loader()
    
    return HealthResponse(
        status="healthy",
        models_loaded=model_loader.is_loaded,
        version=API_VERSION
    )


# Additional endpoint for model reload (admin use)
@app.post(
    "/reload-models",
    response_model=HealthResponse,
    summary="Reload Models",
    description="Force reload all models from disk.",
    include_in_schema=False  # Hidden from public docs
)
async def reload_models() -> HealthResponse:
    """
    Force reload all models from disk.
    
    Returns:
        HealthResponse with updated model loading status.
    """
    logger.info("Reloading all models...")
    model_loader = get_model_loader()
    success = model_loader.reload_models()
    
    return HealthResponse(
        status="healthy" if success else "degraded",
        models_loaded=success,
        version=API_VERSION
    )
