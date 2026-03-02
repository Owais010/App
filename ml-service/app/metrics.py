"""
Metrics — Prometheus-compatible monitoring for ML predictions.

Tracks:
  - Prediction counts (by model type and prediction type)
  - Latency distributions
  - Model accuracy (when actuals are supplied)
  - Feature distribution drift
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# COUNTERS & ACCUMULATORS
# ─────────────────────────────────────────────────────────────────────────────

_counters: dict[str, int] = defaultdict(int)
_latencies: dict[str, list[float]] = defaultdict(list)
_accuracy_buffer: list[dict] = []  # recent predictions with actuals

MAX_LATENCY_BUFFER = 1000
MAX_ACCURACY_BUFFER = 5000


def record_prediction(
    prediction_type: str,
    model_used: str,
    latency_ms: float,
) -> None:
    """Record a prediction event."""
    key = f"{prediction_type}:{model_used}"
    _counters[key] += 1
    _counters[f"total:{prediction_type}"] += 1

    _latencies[key].append(latency_ms)
    if len(_latencies[key]) > MAX_LATENCY_BUFFER:
        _latencies[key] = _latencies[key][-MAX_LATENCY_BUFFER:]


def record_actual(
    prediction_type: str,
    predicted: str,
    actual: str,
    user_id: str,
    topic_id: str,
) -> None:
    """Record actual outcome for a past prediction (for accuracy tracking)."""
    _accuracy_buffer.append(
        {
            "type": prediction_type,
            "predicted": predicted,
            "actual": actual,
            "user_id": user_id,
            "topic_id": topic_id,
            "timestamp": time.time(),
        }
    )
    if len(_accuracy_buffer) > MAX_ACCURACY_BUFFER:
        _accuracy_buffer.pop(0)


def get_metrics_summary() -> dict:
    """Get full metrics summary for /metrics endpoint."""
    summary = {
        "prediction_counts": dict(_counters),
        "latency_stats": {},
        "accuracy": {},
    }

    # Latency percentiles
    for key, values in _latencies.items():
        if not values:
            continue
        import numpy as np

        arr = np.array(values)
        summary["latency_stats"][key] = {
            "count": len(arr),
            "mean_ms": round(float(np.mean(arr)), 2),
            "p50_ms": round(float(np.percentile(arr, 50)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
            "p99_ms": round(float(np.percentile(arr, 99)), 2),
        }

    # Online accuracy (last N predictions with actuals)
    if _accuracy_buffer:
        correct = sum(
            1 for r in _accuracy_buffer if r["predicted"] == r["actual"]
        )
        summary["accuracy"] = {
            "total_evaluated": len(_accuracy_buffer),
            "correct": correct,
            "accuracy": round(correct / len(_accuracy_buffer), 4),
        }

        # Per prediction type
        by_type: dict[str, dict] = {}
        for r in _accuracy_buffer:
            t = r["type"]
            if t not in by_type:
                by_type[t] = {"total": 0, "correct": 0}
            by_type[t]["total"] += 1
            if r["predicted"] == r["actual"]:
                by_type[t]["correct"] += 1

        for t, d in by_type.items():
            d["accuracy"] = (
                round(d["correct"] / d["total"], 4) if d["total"] > 0 else 0
            )
        summary["accuracy"]["by_type"] = by_type

    return summary


async def log_prediction_to_db(
    user_id: str,
    topic_id: Optional[str],
    model_name: str,
    model_version: str,
    predicted_level: Optional[str] = None,
    predicted_prob: Optional[float] = None,
    confidence: Optional[float] = None,
    feature_snapshot: Optional[dict] = None,
) -> None:
    """
    Log a prediction to the ml_predictions table for offline evaluation.
    Non-blocking — failures are silently logged.
    """
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return

    url = f"{settings.SUPABASE_URL}/rest/v1/ml_predictions"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload = {
        "user_id": user_id,
        "topic_id": topic_id,
        "model_name": model_name,
        "model_version": model_version,
        "predicted_level": predicted_level,
        "predicted_prob": predicted_prob,
        "confidence": confidence,
        "feature_snapshot": feature_snapshot,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code not in (200, 201):
                logger.debug(
                    "Failed to log prediction: %s %s",
                    resp.status_code,
                    resp.text,
                )
    except Exception as e:
        logger.debug("Prediction logging error (non-fatal): %s", e)
