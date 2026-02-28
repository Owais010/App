"""
Model Loader module for the Adaptive Learning Intelligence Engine.

Handles loading and caching of trained ML models from disk.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import joblib

from app.config import (
    SKILL_GAP_MODEL_PATH,
    DIFFICULTY_MODEL_PATH,
    RANKING_MODEL_PATH
)


logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton-like model loader that caches loaded models in memory.
    
    Models are loaded once and reused for all predictions to minimize
    disk I/O and improve response times.
    """
    
    _instance: Optional["ModelLoader"] = None
    _models: Dict[str, Any] = {}
    _loaded: bool = False
    
    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the model loader."""
        self._model_paths = {
            "skill_gap": SKILL_GAP_MODEL_PATH,
            "difficulty": DIFFICULTY_MODEL_PATH,
            "ranking": RANKING_MODEL_PATH
        }
    
    def load_all_models(self) -> bool:
        """
        Load all models from disk into memory.
        
        Returns:
            True if all models loaded successfully, False otherwise.
        """
        if self._loaded:
            logger.debug("Models already loaded, skipping reload")
            return True
        
        try:
            for model_name, model_path in self._model_paths.items():
                self._load_model(model_name, model_path)
            
            self._loaded = True
            logger.info("All models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            self._loaded = False
            return False
    
    def _load_model(self, model_name: str, model_path: Path) -> None:
        """
        Load a single model from disk.
        
        Args:
            model_name: Name identifier for the model.
            model_path: Path to the model file.
            
        Raises:
            FileNotFoundError: If model file doesn't exist.
            Exception: If model loading fails.
        """
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        logger.info(f"Loading model '{model_name}' from {model_path}")
        self._models[model_name] = joblib.load(model_path)
        logger.info(f"Model '{model_name}' loaded successfully")
    
    def get_model(self, model_name: str) -> Any:
        """
        Get a loaded model by name.
        
        Args:
            model_name: Name of the model to retrieve.
            
        Returns:
            The loaded model object.
            
        Raises:
            ValueError: If model is not loaded.
        """
        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' not loaded")
        return self._models[model_name]
    
    @property
    def skill_gap_model(self) -> Any:
        """Get the skill gap regression model."""
        return self.get_model("skill_gap")
    
    @property
    def difficulty_model(self) -> Any:
        """Get the difficulty classification model."""
        return self.get_model("difficulty")
    
    @property
    def ranking_model(self) -> Any:
        """Get the ranking scoring model."""
        return self.get_model("ranking")
    
    @property
    def is_loaded(self) -> bool:
        """Check if all models are loaded."""
        return self._loaded
    
    def reload_models(self) -> bool:
        """
        Force reload all models from disk.
        
        Returns:
            True if reload successful, False otherwise.
        """
        self._loaded = False
        self._models = {}
        return self.load_all_models()


# Global model loader instance
model_loader = ModelLoader()


def get_model_loader() -> ModelLoader:
    """
    Get the global model loader instance.
    
    Returns:
        The singleton ModelLoader instance.
    """
    return model_loader
