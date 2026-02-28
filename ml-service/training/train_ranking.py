"""
Training script for the Recommendation Ranking Model.

Model: GradientBoostingRegressor
Target: engagement_success_score

Label formula:
    engagement_score = 0.4 * accuracy_rate + 
                       0.3 * persistence_score + 
                       0.3 * (1 - gap_score)
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

from app.feature_engineering import (
    compute_derived_features,
    get_feature_names,
    compute_gap_score_label,
    compute_engagement_score
)
from app.config import RANKING_MODEL_PATH

# -----------------------------------------------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "attempt_count",
    "correct_attempts",
    "avg_response_time",
    "self_confidence_rating",
    "difficulty_feedback",
    "session_duration",
    "previous_mastery_score",
    "time_since_last_attempt"
]

MIN_SAMPLES = 100
TEST_SIZE = 0.2
RANDOM_STATE = 42
CV_FOLDS = 5

# Exportable functions for external use
__all__ = [
    "load_and_prepare_data",
    "prepare_from_dataframe",
    "train_model",
    "save_model",
    "main"
]


# -----------------------------------------------------------------------------
# DATA VALIDATION
# -----------------------------------------------------------------------------
def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean the input DataFrame.
    
    Args:
        df: Raw input DataFrame.
        
    Returns:
        Validated and cleaned DataFrame.
        
    Raises:
        ValueError: If validation fails critically.
    """
    # Check for required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check minimum sample size
    if len(df) < MIN_SAMPLES:
        raise ValueError(
            f"Insufficient data: {len(df)} samples. "
            f"Need at least {MIN_SAMPLES} samples."
        )
    
    # Handle null values
    null_count = df.isnull().sum().sum()
    if null_count > 0:
        logger.warning(f"Found {null_count} null values in dataset")
        rows_before = len(df)
        df = df.dropna(subset=REQUIRED_COLUMNS)
        rows_dropped = rows_before - len(df)
        logger.warning(f"Dropped {rows_dropped} rows with null values")
        
        # Re-check minimum samples after dropping nulls
        if len(df) < MIN_SAMPLES:
            raise ValueError(
                f"Insufficient data after null removal: {len(df)} samples. "
                f"Need at least {MIN_SAMPLES} samples."
            )
    
    # Validate numeric ranges
    if (df["attempt_count"] <= 0).any():
        invalid_count = (df["attempt_count"] <= 0).sum()
        logger.warning(f"Found {invalid_count} rows with attempt_count <= 0, filtering out")
        df = df[df["attempt_count"] > 0]
    
    if (df["session_duration"] <= 0).any():
        invalid_count = (df["session_duration"] <= 0).sum()
        logger.warning(f"Found {invalid_count} rows with session_duration <= 0, filtering out")
        df = df[df["session_duration"] > 0]
    
    # Validate correct_attempts <= attempt_count
    invalid_attempts = df["correct_attempts"] > df["attempt_count"]
    if invalid_attempts.any():
        invalid_count = invalid_attempts.sum()
        logger.warning(f"Found {invalid_count} rows where correct_attempts > attempt_count, capping")
        df.loc[invalid_attempts, "correct_attempts"] = df.loc[invalid_attempts, "attempt_count"]
    
    # Final sample count check
    if len(df) < MIN_SAMPLES:
        raise ValueError(
            f"Insufficient valid data: {len(df)} samples after cleaning. "
            f"Need at least {MIN_SAMPLES} samples."
        )
    
    logger.info(f"Validation complete: {len(df)} valid samples")
    return df.reset_index(drop=True)


def compute_features_safe(input_data: dict) -> Tuple[list, dict]:
    """
    Compute features with safe division handling.
    
    Args:
        input_data: Dictionary containing raw input features.
        
    Returns:
        Tuple of (feature_vector, derived_features_dict).
    """
    # Safe division helper
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        if denominator == 0 or denominator is None:
            return default
        return numerator / denominator
    
    # Compute derived features safely
    attempt_count = input_data["attempt_count"]
    correct_attempts = input_data["correct_attempts"]
    session_duration = input_data["session_duration"]
    previous_mastery_score = input_data["previous_mastery_score"]
    self_confidence_rating = input_data["self_confidence_rating"]
    difficulty_feedback = input_data["difficulty_feedback"]
    
    # Safe computations
    accuracy_rate = safe_divide(correct_attempts, attempt_count, 0.0)
    accuracy_rate = np.clip(accuracy_rate, 0.0, 1.0)
    
    failure_rate = 1.0 - accuracy_rate
    
    learning_velocity = safe_divide(previous_mastery_score, session_duration, 0.0)
    
    confidence_performance_gap = self_confidence_rating - accuracy_rate
    
    difficulty_stress_index = difficulty_feedback * failure_rate
    
    persistence_score = safe_divide(session_duration, (attempt_count + 1), 0.0)
    
    derived = {
        "accuracy_rate": accuracy_rate,
        "failure_rate": failure_rate,
        "learning_velocity": learning_velocity,
        "confidence_performance_gap": confidence_performance_gap,
        "difficulty_stress_index": difficulty_stress_index,
        "persistence_score": persistence_score
    }
    
    # Build feature vector
    feature_vector = [
        input_data["attempt_count"],
        input_data["correct_attempts"],
        input_data["avg_response_time"],
        input_data["self_confidence_rating"],
        input_data["difficulty_feedback"],
        input_data["session_duration"],
        input_data["previous_mastery_score"],
        input_data["time_since_last_attempt"],
        derived["accuracy_rate"],
        derived["failure_rate"],
        derived["learning_velocity"],
        derived["confidence_performance_gap"],
        derived["difficulty_stress_index"],
        derived["persistence_score"]
    ]
    
    return feature_vector, derived


# -----------------------------------------------------------------------------
# DATA PREPARATION
# -----------------------------------------------------------------------------
def prepare_from_dataframe(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and labels from a DataFrame.
    
    This function allows programmatic use from train_all.py or tests.
    
    Args:
        df: Input DataFrame with required columns.
        
    Returns:
        Tuple of (X features array, y labels array).
    """
    # Validate DataFrame
    df = validate_dataframe(df)
    
    X_list = []
    y_list = []
    skipped_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Create input dict from row
            input_data = {
                "attempt_count": float(row["attempt_count"]),
                "correct_attempts": float(row["correct_attempts"]),
                "avg_response_time": float(row["avg_response_time"]),
                "self_confidence_rating": float(row["self_confidence_rating"]),
                "difficulty_feedback": float(row["difficulty_feedback"]),
                "session_duration": float(row["session_duration"]),
                "previous_mastery_score": float(row["previous_mastery_score"]),
                "time_since_last_attempt": float(row["time_since_last_attempt"])
            }
            
            # Compute derived features safely
            feature_vector, derived = compute_features_safe(input_data)
            
            # Compute gap score first (needed for engagement score)
            gap_score = compute_gap_score_label(derived, input_data["previous_mastery_score"])
            gap_score = np.clip(gap_score, 0.0, 1.0)
            
            # Compute engagement score label
            engagement_score = compute_engagement_score(
                accuracy_rate=derived["accuracy_rate"],
                persistence_score=derived["persistence_score"],
                gap_score=gap_score
            )
            
            # Clip engagement score to valid range [0, 1]
            engagement_score = np.clip(engagement_score, 0.0, 1.0)
            
            X_list.append(feature_vector)
            y_list.append(engagement_score)
            
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to error: {e}")
            skipped_count += 1
            continue
    
    if skipped_count > 0:
        logger.warning(f"Skipped {skipped_count} rows during processing")
    
    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.float64)
    
    # Validate feature count matches expected
    feature_names = get_feature_names()
    assert len(feature_names) == X.shape[1], (
        f"Feature name count {len(feature_names)} "
        f"does not match feature vector size {X.shape[1]}"
    )
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Label vector shape: {y.shape}")
    logger.info(f"Labels range: [{y.min():.4f}, {y.max():.4f}]")
    logger.info(f"Labels mean: {y.mean():.4f}, std: {y.std():.4f}")
    
    return X, y


def load_and_prepare_data(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load dataset from CSV and prepare features and labels.
    
    Args:
        csv_path: Path to the CSV dataset.
        
    Returns:
        Tuple of (X features array, y labels array).
    """
    logger.info(f"Loading dataset from {csv_path}...")
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"Dataset file is empty: {csv_path}")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    logger.info(f"Loaded {len(df)} raw samples")
    
    return prepare_from_dataframe(df)


# -----------------------------------------------------------------------------
# MODEL TRAINING
# -----------------------------------------------------------------------------
def train_model(
    X: np.ndarray, 
    y: np.ndarray,
    perform_cv: bool = True
) -> Tuple[GradientBoostingRegressor, dict]:
    """
    Train the ranking regression model.
    
    Args:
        X: Feature matrix.
        y: Label vector.
        perform_cv: Whether to perform cross-validation.
        
    Returns:
        Tuple of (trained model, metrics dictionary).
    """
    logger.info(f"Splitting dataset ({int((1-TEST_SIZE)*100)}% train, {int(TEST_SIZE*100)}% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Test samples: {len(X_test)}")
    
    logger.info("Training GradientBoostingRegressor...")
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=RANDOM_STATE,
        loss='squared_error'
    )
    
    model.fit(X_train, y_train)
    logger.info("Training complete!")
    
    # ---------------------------------------------------------------------
    # EVALUATION
    # ---------------------------------------------------------------------
    logger.info("=" * 50)
    logger.info("EVALUATION METRICS")
    logger.info("=" * 50)
    
    # Train set predictions (for overfitting detection)
    y_train_pred = model.predict(X_train)
    y_train_pred = np.clip(y_train_pred, 0.0, 1.0)
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    
    # Test set predictions
    y_test_pred = model.predict(X_test)
    y_test_pred = np.clip(y_test_pred, 0.0, 1.0)
    
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_r2 = r2_score(y_test, y_test_pred)
    
    # Print comparison for overfitting detection
    logger.info(f"Train MAE: {train_mae:.4f}  |  Test MAE: {test_mae:.4f}")
    logger.info(f"Train RMSE: {train_rmse:.4f}  |  Test RMSE: {test_rmse:.4f}")
    logger.info(f"Train R2: {train_r2:.4f}  |  Test R2: {test_r2:.4f}")
    
    # Overfitting warning
    r2_gap = train_r2 - test_r2
    if r2_gap > 0.1:
        logger.warning(
            f"Potential overfitting detected! "
            f"Train-Test R2 gap: {r2_gap:.4f}"
        )
    
    # Cross-validation
    cv_mean = None
    cv_std = None
    if perform_cv:
        logger.info("=" * 50)
        logger.info(f"CROSS-VALIDATION ({CV_FOLDS}-Fold)")
        logger.info("=" * 50)
        
        cv_scores = cross_val_score(
            model, X, y, cv=CV_FOLDS, scoring='r2'
        )
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()
        
        logger.info(f"CV R2 Scores: {[round(s, 4) for s in cv_scores]}")
        logger.info(f"CV R2 Mean: {cv_mean:.4f} ± {cv_std:.4f}")
    
    # Feature importance
    logger.info("=" * 50)
    logger.info("FEATURE IMPORTANCE (Top 10)")
    logger.info("=" * 50)
    
    feature_names = get_feature_names()
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    for i, idx in enumerate(indices[:10]):
        logger.info(f"{i+1}. {feature_names[idx]}: {importances[idx]:.4f}")
    
    # Build metrics dictionary
    metrics = {
        "train_mae": round(train_mae, 4),
        "train_rmse": round(train_rmse, 4),
        "train_r2": round(train_r2, 4),
        "test_mae": round(test_mae, 4),
        "test_rmse": round(test_rmse, 4),
        "test_r2": round(test_r2, 4),
        "cv_r2_mean": round(cv_mean, 4) if cv_mean else None,
        "cv_r2_std": round(cv_std, 4) if cv_std else None,
        "feature_importance": {
            feature_names[i]: round(importances[i], 4) 
            for i in indices
        }
    }
    
    return model, metrics


# -----------------------------------------------------------------------------
# MODEL PERSISTENCE
# -----------------------------------------------------------------------------
def save_model(
    model: GradientBoostingRegressor, 
    path: Path,
    metrics: dict,
    n_samples: int
) -> None:
    """
    Save the trained model and metadata to disk.
    
    Args:
        model: Trained model.
        path: Path to save the model.
        metrics: Training metrics dictionary.
        n_samples: Number of samples used for training.
    """
    # Ensure models directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    logger.info(f"Saving model to {path}...")
    joblib.dump(model, path)
    logger.info("Model saved successfully!")
    
    # Save metadata
    metadata = {
        "model_type": "GradientBoostingRegressor",
        "target": "engagement_success_score",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": n_samples,
        "n_features": len(get_feature_names()),
        "feature_names": get_feature_names(),
        "hyperparameters": {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 5,
            "random_state": RANDOM_STATE,
            "loss": "squared_error"
        },
        "metrics": metrics,
        "label_formula": (
            "engagement_score = 0.4 * accuracy_rate + "
            "0.3 * persistence_score + 0.3 * (1 - gap_score)"
        )
    }
    
    meta_path = path.with_suffix(".json")
    logger.info(f"Saving metadata to {meta_path}...")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Metadata saved successfully!")


# -----------------------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------
def main(csv_path: Optional[str] = None) -> None:
    """
    Main training pipeline.
    
    Args:
        csv_path: Optional path to CSV dataset. If None, uses default path.
    """
    logger.info("=" * 60)
    logger.info("RANKING MODEL TRAINING")
    logger.info("=" * 60)
    
    # Determine dataset path
    if csv_path is None:
        csv_path = Path(__file__).parent.parent / "data" / "training_data.csv"
    else:
        csv_path = Path(csv_path)
    
    # Allow command line override
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    
    if not csv_path.exists():
        logger.error(f"Dataset not found at {csv_path}")
        logger.error("Please provide a valid CSV path or generate training data first.")
        logger.error("Usage: python train_ranking.py [path/to/data.csv]")
        sys.exit(1)
    
    try:
        # Load and prepare data
        X, y = load_and_prepare_data(str(csv_path))
        
        # Train model
        model, metrics = train_model(X, y, perform_cv=True)
        
        # Save model and metadata
        save_model(model, RANKING_MODEL_PATH, metrics, n_samples=len(X))
        
        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 60)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
