"""
Feature Engineering — Extract, transform, and cache ML features.

Produces the 14-dimensional feature vector used by all models.
Matches the SQL `compute_ml_features` RPC exactly.

Feature list:
  1.  total_attempts      — total answers on this topic
  2.  correct_attempts    — total correct on this topic
  3.  accuracy            — correct / total
  4.  weighted_score      — difficulty-weighted cumulative score
  5.  recent_accuracy     — accuracy over last 10 answers
  6.  accuracy_trend      — recent_accuracy - accuracy (positive = improving)
  7.  streak_length       — consecutive correct or incorrect from most recent
  8.  avg_time_per_q      — average seconds per question
  9.  days_since_last     — days since last answer on topic (-1 if never)
  10. easy_accuracy       — accuracy on easy questions
  11. medium_accuracy     — accuracy on medium questions
  12. hard_accuracy       — accuracy on hard questions
  13. global_accuracy     — user's overall accuracy across all topics
  14. topics_attempted    — distinct topics this user has answered
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np
import httpx

from app.config import get_settings
from app.schemas import FeatureVector

logger = logging.getLogger(__name__)

# Feature names in canonical order (must match training column order)
FEATURE_NAMES = [
    "total_attempts",
    "correct_attempts",
    "accuracy",
    "weighted_score",
    "recent_accuracy",
    "accuracy_trend",
    "streak_length",
    "avg_time_per_q",
    "days_since_last",
    "easy_accuracy",
    "medium_accuracy",
    "hard_accuracy",
    "global_accuracy",
    "topics_attempted",
]

# In-memory cache: (user_id, topic_id) -> (timestamp, FeatureVector)
_cache: dict[tuple[str, str], tuple[float, FeatureVector]] = {}


def feature_vector_to_array(fv: FeatureVector) -> np.ndarray:
    """Convert FeatureVector to numpy array in canonical column order."""
    return np.array(
        [getattr(fv, name) for name in FEATURE_NAMES],
        dtype=np.float64,
    )


def _empty_features() -> FeatureVector:
    """Return a zero-initialized feature vector for cold-start users."""
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


async def get_features(
    user_id: str,
    topic_id: str,
    precomputed: Optional[FeatureVector] = None,
) -> FeatureVector:
    """
    Get features for a (user, topic) pair.

    Priority:
      1. precomputed — caller already has them (e.g. from request body)
      2. in-memory cache — if fresh enough
      3. Supabase RPC `compute_ml_features` — canonical source
      4. Supabase `ml_feature_cache` table — stale but usable
      5. Direct SQL queries — fallback
      6. Empty vector — cold start
    """
    if precomputed is not None:
        return precomputed

    # Check in-memory cache
    settings = get_settings()
    cache_key = (user_id, topic_id)
    if cache_key in _cache:
        cached_time, cached_fv = _cache[cache_key]
        if time.time() - cached_time < settings.FEATURE_CACHE_TTL_SECONDS:
            return cached_fv

    # Try RPC
    fv = await _fetch_features_rpc(user_id, topic_id)
    if fv is not None:
        _cache[cache_key] = (time.time(), fv)
        return fv

    # Try feature cache table
    fv = await _fetch_features_table(user_id, topic_id)
    if fv is not None:
        _cache[cache_key] = (time.time(), fv)
        return fv

    # Try direct queries
    fv = await _compute_features_direct(user_id, topic_id)
    if fv is not None:
        _cache[cache_key] = (time.time(), fv)
        return fv

    # Cold start
    logger.info("Cold start for user=%s topic=%s", user_id, topic_id)
    return _empty_features()


async def get_features_batch(
    user_id: str,
    topic_ids: list[str],
) -> dict[str, FeatureVector]:
    """Get features for multiple topics in parallel."""
    results = {}
    for tid in topic_ids:
        results[tid] = await get_features(user_id, tid)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL: Data fetching strategies
# ─────────────────────────────────────────────────────────────────────────────

def _has_valid_supabase_config() -> bool:
    """Check if Supabase credentials are configured (not placeholders)."""
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        return False
    # Reject placeholder keys
    if settings.SUPABASE_SERVICE_KEY.startswith("sb_secret_"):
        return False
    return True


def _supabase_headers() -> dict[str, str]:
    """Build Supabase REST headers."""
    settings = get_settings()
    return {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }


async def _fetch_features_rpc(
    user_id: str, topic_id: str
) -> Optional[FeatureVector]:
    """Call Supabase RPC `compute_ml_features`."""
    if not _has_valid_supabase_config():
        return None

    settings = get_settings()
    url = f"{settings.SUPABASE_URL}/rest/v1/rpc/compute_ml_features"
    payload = {"p_user_id": user_id, "p_topic_id": topic_id}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url, json=payload, headers=_supabase_headers()
            )
            if resp.status_code != 200:
                logger.warning("RPC compute_ml_features failed: %s", resp.text)
                return None

            data = resp.json()
            if not data or isinstance(data, list):
                return None

            return FeatureVector(
                total_attempts=data.get("total_attempts", 0),
                correct_attempts=data.get("correct_attempts", 0),
                accuracy=data.get("accuracy", 0.0),
                weighted_score=data.get("weighted_score", 0.0),
                recent_accuracy=data.get("recent_accuracy", 0.0),
                accuracy_trend=data.get("accuracy_trend", 0.0),
                streak_length=data.get("streak_length", 0),
                avg_time_per_q=data.get("avg_time_per_q", 0.0),
                days_since_last=data.get("days_since_last", -1.0),
                easy_accuracy=data.get("easy_accuracy", 0.0),
                medium_accuracy=data.get("medium_accuracy", 0.0),
                hard_accuracy=data.get("hard_accuracy", 0.0),
                global_accuracy=data.get("global_accuracy", 0.0),
                topics_attempted=data.get("topics_attempted", 0),
            )
    except Exception as e:
        logger.warning("RPC feature fetch error: %s", e)
        return None


async def _fetch_features_table(
    user_id: str, topic_id: str
) -> Optional[FeatureVector]:
    """Read pre-computed features from ml_feature_cache table."""
    if not _has_valid_supabase_config():
        return None

    settings = get_settings()

    url = (
        f"{settings.SUPABASE_URL}/rest/v1/ml_feature_cache"
        f"?user_id=eq.{user_id}&topic_id=eq.{topic_id}"
        f"&select=*&limit=1"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=_supabase_headers())
            if resp.status_code != 200:
                return None

            rows = resp.json()
            if not rows:
                return None

            row = rows[0]
            return FeatureVector(
                total_attempts=row.get("total_attempts", 0),
                correct_attempts=row.get("correct_attempts", 0),
                accuracy=row.get("accuracy", 0.0),
                weighted_score=row.get("weighted_score", 0.0),
                recent_accuracy=row.get("recent_accuracy", 0.0),
                accuracy_trend=row.get("accuracy_trend", 0.0),
                streak_length=row.get("streak_length", 0),
                avg_time_per_q=row.get("avg_time_per_q", 0.0),
                days_since_last=row.get("days_since_last", -1.0),
                easy_accuracy=row.get("easy_accuracy", 0.0),
                medium_accuracy=row.get("medium_accuracy", 0.0),
                hard_accuracy=row.get("hard_accuracy", 0.0),
                global_accuracy=row.get("global_accuracy", 0.0),
                topics_attempted=row.get("topics_attempted", 0),
            )
    except Exception as e:
        logger.warning("Feature cache table fetch error: %s", e)
        return None


async def _compute_features_direct(
    user_id: str, topic_id: str
) -> Optional[FeatureVector]:
    """
    Compute features from raw user_answers + user_topic_stats tables.
    Used when the RPC and cache table aren't available yet (pre-migration).
    """
    if not _has_valid_supabase_config():
        return None

    settings = get_settings()
    headers = _supabase_headers()
    base = settings.SUPABASE_URL

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Fetch user_topic_stats for this topic
            stats_resp = await client.get(
                f"{base}/rest/v1/user_topic_stats"
                f"?user_id=eq.{user_id}&topic_id=eq.{topic_id}"
                f"&select=attempts,correct,weighted_score,accuracy"
                f"&limit=1",
                headers=headers,
            )
            stats = (
                stats_resp.json()[0]
                if stats_resp.status_code == 200 and stats_resp.json()
                else {}
            )

            # Fetch recent answers for this topic (last 20 for trend calc)
            answers_resp = await client.get(
                f"{base}/rest/v1/user_answers"
                f"?user_id=eq.{user_id}&topic_id=eq.{topic_id}"
                f"&select=is_correct,difficulty,time_taken,answered_at"
                f"&order=answered_at.desc&limit=20",
                headers=headers,
            )
            answers = (
                answers_resp.json()
                if answers_resp.status_code == 200
                else []
            )

            # Fetch global stats
            global_resp = await client.get(
                f"{base}/rest/v1/user_topic_stats"
                f"?user_id=eq.{user_id}"
                f"&select=attempts,correct",
                headers=headers,
            )
            global_stats = (
                global_resp.json()
                if global_resp.status_code == 200
                else []
            )

        total = stats.get("attempts", 0)
        correct = stats.get("correct", 0)
        accuracy = stats.get("accuracy", 0.0) or (
            correct / total if total > 0 else 0.0
        )
        weighted = stats.get("weighted_score", 0.0)

        # Recent accuracy (last 10)
        recent = answers[:10]
        recent_correct = sum(
            1 for a in recent if a.get("is_correct") is True
        )
        recent_acc = (
            recent_correct / len(recent) if recent else 0.0
        )

        # Streak
        streak = 0
        if answers:
            first_result = answers[0].get("is_correct")
            for a in answers:
                if a.get("is_correct") == first_result:
                    streak += 1
                else:
                    break

        # Average time
        times = [
            a.get("time_taken", 0)
            for a in answers
            if a.get("time_taken") and a["time_taken"] > 0
        ]
        avg_time = np.mean(times) if times else 0.0

        # Days since last
        days_since = -1.0
        if answers and answers[0].get("answered_at"):
            from datetime import datetime, timezone

            last_dt = datetime.fromisoformat(
                answers[0]["answered_at"].replace("Z", "+00:00")
            )
            days_since = (
                datetime.now(timezone.utc) - last_dt
            ).total_seconds() / 86400.0

        # Difficulty breakdown
        def diff_acc(diff: str) -> float:
            subset = [
                a for a in answers if a.get("difficulty") == diff
            ]
            if not subset:
                return 0.0
            return sum(
                1 for a in subset if a.get("is_correct") is True
            ) / len(subset)

        # Global accuracy
        g_total = sum(s.get("attempts", 0) for s in global_stats)
        g_correct = sum(s.get("correct", 0) for s in global_stats)
        global_acc = g_correct / g_total if g_total > 0 else 0.0

        return FeatureVector(
            total_attempts=total,
            correct_attempts=correct,
            accuracy=round(accuracy, 4),
            weighted_score=round(weighted, 4),
            recent_accuracy=round(recent_acc, 4),
            accuracy_trend=round(recent_acc - accuracy, 4),
            streak_length=streak,
            avg_time_per_q=round(float(avg_time), 2),
            days_since_last=round(days_since, 2),
            easy_accuracy=round(diff_acc("easy"), 4),
            medium_accuracy=round(diff_acc("medium"), 4),
            hard_accuracy=round(diff_acc("hard"), 4),
            global_accuracy=round(global_acc, 4),
            topics_attempted=len(global_stats),
        )

    except Exception as e:
        logger.warning("Direct feature computation error: %s", e)
        return None


def invalidate_cache(user_id: str, topic_id: Optional[str] = None) -> None:
    """Invalidate cached features after new answers are recorded."""
    if topic_id:
        _cache.pop((user_id, topic_id), None)
    else:
        keys_to_remove = [k for k in _cache if k[0] == user_id]
        for k in keys_to_remove:
            _cache.pop(k, None)
