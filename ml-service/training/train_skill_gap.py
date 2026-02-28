"""
Training script for the Skill Gap Regression Model.

Model: GradientBoostingRegressor
Target: gap_score ∈ [0,1]

Label formula:
    gap_score = 0.5 * failure_rate + 
                0.3 * (1 - previous_mastery_score) + 
                0.2 * abs(confidence_performance_gap)
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
    compute_gap_score_label
)
from app.config import SKILL_GAP_MODEL_PATH

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
    """Validate and clean the input DataFrame."""
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if len(df) < MIN_SAMPLES:
        raise ValueError(f"Insufficient data: {len(df)} samples. Need at least {MIN_SAMPLES}.")
    
    null_count = df.isnull().sum().sum()
    if null_count > 0:
        logger.warning(f"Found {null_count} null values in dataset")
        rows_before = len(df)
        df = df.dropna(subset=REQUIRED_COLUMNS)
        logger.warning(f"Dropped {rows_before - len(df)} rows with null values")
        
        if len(df) < MIN_SAMPLES:
            raise ValueError(f"Insufficient data after null removal: {len(df)} samples.")
    
    if (df["attempt_count"] <= 0).any():
        logger.warning("Filtering rows with attempt_count <= 0")
        df = df[df["attempt_count"] > 0]
    
    if (df["session_duration"] <= 0).any():
        logger.warning("Filtering rows with session_duration <= 0")
        df = df[df["session_duration"] > 0]
    
    invalid_attempts = df["correct_attempts"] > df["attempt_count"]
    if invalid_attempts.any():
        logger.warning(f"Capping {invalid_attempts.sum()} rows where correct_attempts > attempt_count")
        df.loc[invalid_attempts, "correct_attempts"] = df.loc[invalid_attempts, "attempt_count"]
    
    logger.info(f"Validation complete: {len(df)} valid samples")
    return df.reset_index(drop=True)


def compute_features_safe(input_data: dict) -> Tuple[list, dict]:
    """Compute features with safe division handling."""
    def safe_divide(num: float, denom: float, default: float = 0.0) -> float:
        return num / denom if denom and denom != 0 else default
    
    attempt_count = input_data["attempt_count"]
    correct_attempts = input_data["correct_attempts"]
    session_duration = input_data["session_duration"]
    previous_mastery_score = input_data["previous_mastery_score"]
    self_confidence_rating = input_data["self_confidence_rating"]
    difficulty_feedback = input_data["difficulty_feedback"]
    
    accuracy_rate = np.clip(safe_divide(correct_attempts, attempt_count), 0.0, 1.0)
    failure_rate = 1.0 - accuracy_rate
    learning_velocity = safe_divide(previous_mastery_score, session_duration)
    confidence_performance_gap = self_confidence_rating - accuracy_rate
    difficulty_stress_index = difficulty_feedback * failure_rate
    persistence_score = safe_divide(session_duration, (attempt_count + 1))
    
    derived = {
        "accuracy_rate": accuracy_rate,
        "failure_rate": failure_rate,
        "learning_velocity": learning_velocity,
        "confidence_performance_gap": confidence_performance_gap,
        "difficulty_stress_index": difficulty_stress_index,
        "persistence_score": persistence_score
    }
    
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
    """Prepare features and labels from a DataFrame."""
    df = validate_dataframe(df)
    
    X_list = []
    y_list = []
    skipped = 0
    
    for idx, row in df.iterrows():
        try:
            input_data = {col: float(row[col]) for col in REQUIRED_COLUMNS}
            feature_vector, derived = compute_features_safe(input_data)
            gap_score = compute_gap_score_label(derived, input_data["previous_mastery_score"])
            gap_score = np.clip(gap_score, 0.0, 1.0)
            
            X_list.append(feature_vector)
            y_list.append(gap_score)
        except Exception as e:
            logger.warning(f"Skipping row {idx}: {e}")
            skipped += 1
    
    if skipped > 0:
        logger.warning(f"Skipped {skipped} rows during processing")
    
    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list, dtype=np.float64)
    
    feature_names = get_feature_names()
    assert len(feature_names) == X.shape[1], "Feature count mismatch"
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Labels range: [{y.min():.4f}, {y.max():.4f}]")
    
    return X, y


def load_and_prepare_data(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Load dataset from CSV and prepare features and labels."""
    logger.info(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} raw samples")
    return prepare_from_dataframe(df)


# -----------------------------------------------------------------------------
# MODEL TRAINING
# -----------------------------------------------------------------------------
def train_model(X: np.ndarray, y: np.ndarray, perform_cv: bool = True) -> Tuple[GradientBoostingRegressor, dict]:
    """Train the skill gap regression model."""
    logger.info(f"Splitting dataset ({int((1-TEST_SIZE)*100)}% train, {int(TEST_SIZE*100)}% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    logger.info(f"Training: {len(X_train)}, Test: {len(X_test)}")
    
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
    
    # Evaluation
    logger.info("=" * 50)
    logger.info("EVALUATION METRICS")
    logger.info("=" * 50)
    
    y_train_pred = np.clip(model.predict(X_train), 0.0, 1.0)
    y_test_pred = np.clip(model.predict(X_test), 0.0, 1.0)
    
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_r2 = r2_score(y_test, y_test_pred)
    
    logger.info(f"Train MAE: {train_mae:.4f}  |  Test MAE: {test_mae:.4f}")
    logger.info(f"Train RMSE: {train_rmse:.4f}  |  Test RMSE: {test_rmse:.4f}")
    logger.info(f"Train R2: {train_r2:.4f}  |  Test R2: {test_r2:.4f}")
    
    if train_r2 - test_r2 > 0.1:
        logger.warning(f"Potential overfitting! Train-Test R2 gap: {train_r2 - test_r2:.4f}")
    
    cv_mean, cv_std = None, None
    if perform_cv:
        logger.info("=" * 50)
        logger.info(f"CROSS-VALIDATION ({CV_FOLDS}-Fold)")
        logger.info("=" * 50)
        cv_scores = cross_val_score(model, X, y, cv=CV_FOLDS, scoring='r2')
        cv_mean, cv_std = cv_scores.mean(), cv_scores.std()
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
    
    metrics = {
        "train_mae": round(train_mae, 4),
        "train_rmse": round(train_rmse, 4),
        "train_r2": round(train_r2, 4),
        "test_mae": round(test_mae, 4),
        "test_rmse": round(test_rmse, 4),
        "test_r2": round(test_r2, 4),
        "cv_r2_mean": round(cv_mean, 4) if cv_mean else None,
        "cv_r2_std": round(cv_std, 4) if cv_std else None,
    }
    
    return model, metrics


# -----------------------------------------------------------------------------
# MODEL PERSISTENCE
# -----------------------------------------------------------------------------
def save_model(model: GradientBoostingRegressor, path: Path, metrics: dict, n_samples: int) -> None:
    """Save the trained model and metadata to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving model to {path}...")
    joblib.dump(model, path)
    logger.info("Model saved!")
    
    metadata = {
        "model_type": "GradientBoostingRegressor",
        "target": "skill_gap_score",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": n_samples,
        "n_features": len(get_feature_names()),
        "feature_names": get_feature_names(),
        "hyperparameters": {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 5,
            "random_state": RANDOM_STATE,
        },
        "metrics": metrics,
    }
    
    meta_path = path.with_suffix(".json")
    logger.info(f"Saving metadata to {meta_path}...")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main(csv_path: Optional[str] = None) -> None:
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("SKILL GAP MODEL TRAINING")
    logger.info("=" * 60)
    
    if csv_path is None:
        csv_path = Path(__file__).parent.parent / "data" / "training_data.csv"
    else:
        csv_path = Path(csv_path)
    
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    
    if not csv_path.exists():
        logger.error(f"Dataset not found: {csv_path}")
        sys.exit(1)
    
    try:
        X, y = load_and_prepare_data(str(csv_path))
        model, metrics = train_model(X, y)
        save_model(model, SKILL_GAP_MODEL_PATH, metrics, len(X))
        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
