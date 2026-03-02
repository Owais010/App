"""
Model Loader — Load, cache, and manage ML models.

Supports hot-reloading and versioned model registry.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import joblib

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LoadedModel:
    """Container for a loaded model with metadata."""

    name: str
    version: str
    model: Any
    feature_names: list[str] = field(default_factory=list)
    label_encoder: Any = None  # for classification models
    metrics: dict[str, float] = field(default_factory=dict)


class ModelRegistry:
    """
    Thread-safe model registry.

    Loads models from disk (joblib format) and keeps them in memory
    for fast inference. Supports versioned model replacement.
    """

    def __init__(self) -> None:
        self._models: dict[str, LoadedModel] = {}

    def load_model(
        self,
        name: str,
        path: str,
        version: str = "1.0.0",
    ) -> bool:
        """Load a model from a joblib file."""
        try:
            if not os.path.exists(path):
                logger.warning("Model file not found: %s", path)
                return False

            bundle = joblib.load(path)

            # Support both raw models and bundled dicts
            if isinstance(bundle, dict):
                model = bundle.get("model")
                feature_names = bundle.get("feature_names", [])
                label_encoder = bundle.get("label_encoder")
                metrics = bundle.get("metrics", {})
                version = bundle.get("version", version)
            else:
                model = bundle
                feature_names = []
                label_encoder = None
                metrics = {}

            self._models[name] = LoadedModel(
                name=name,
                version=version,
                model=model,
                feature_names=feature_names,
                label_encoder=label_encoder,
                metrics=metrics,
            )
            logger.info("Loaded model %s v%s from %s", name, version, path)
            return True

        except Exception as e:
            logger.error("Failed to load model %s: %s", name, e)
            return False

    def get_model(self, name: str) -> Optional[LoadedModel]:
        """Get a loaded model by name."""
        return self._models.get(name)

    def is_loaded(self, name: str) -> bool:
        """Check if a model is loaded."""
        return name in self._models

    def list_models(self) -> dict[str, bool]:
        """List all expected models and their load status."""
        expected = ["level_classifier", "difficulty_recommender"]
        return {name: name in self._models for name in expected}

    def unload(self, name: str) -> None:
        """Unload a model from memory."""
        self._models.pop(name, None)


# Singleton registry
registry = ModelRegistry()


def load_all_models() -> dict[str, bool]:
    """
    Attempt to load all models at startup.

    Returns dict of model_name -> loaded successfully.
    Won't crash if models don't exist yet (pre-training).
    """
    settings = get_settings()
    model_dir = Path(settings.MODEL_DIR)

    results = {}

    # Level classifier (XGBoost)
    lc_path = model_dir / "level_classifier.joblib"
    results["level_classifier"] = registry.load_model(
        "level_classifier", str(lc_path)
    )

    # Difficulty recommender (LightGBM)
    dr_path = model_dir / "difficulty_recommender.joblib"
    results["difficulty_recommender"] = registry.load_model(
        "difficulty_recommender", str(dr_path)
    )

    loaded = sum(1 for v in results.values() if v)
    logger.info("Loaded %d/%d models", loaded, len(results))

    return results
