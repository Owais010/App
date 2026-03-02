"""
Train Level Classifier — XGBoost multiclass model.

Predicts: beginner / intermediate / advanced
Features: 14-dimensional feature vector

Outputs:
  models/level_classifier.joblib  — bundled model + metadata

Usage:
    python -m training.train_level_classifier
    python -m training.train_level_classifier --data data/training_data.csv
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

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


def train_level_classifier(
    data_path: str = "data/training_data.csv",
    output_path: str = "models/level_classifier.joblib",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """
    Train XGBoost level classifier with full evaluation.

    Returns metrics dict.
    """
    logger.info("Loading data from %s", data_path)
    df = pd.read_csv(data_path)
    logger.info("Dataset: %d rows, level dist: %s", len(df), df["level"].value_counts().to_dict())

    X = df[FEATURE_NAMES].values
    le = LabelEncoder()
    y = le.fit_transform(df["level"])

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    logger.info("Train: %d, Test: %d", len(X_train), len(X_test))

    # XGBoost with tuned hyperparameters
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="multi:softprob",
        num_class=len(le.classes_),
        eval_metric="mlogloss",
        random_state=random_state,
        n_jobs=-1,
        verbosity=0,
    )

    # Train with early stopping
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")

    # AUC (one-vs-rest)
    try:
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
    except Exception:
        auc = 0.0

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")

    # Baseline: rules-based accuracy
    baseline_preds = []
    for _, row in df.iloc[X_test.shape[0]:].iterrows():
        attempts = row["total_attempts"]
        acc = row["accuracy"]
        if attempts < 5:
            baseline_preds.append("beginner")
        elif acc < 0.5:
            baseline_preds.append("beginner")
        elif acc < 0.75:
            baseline_preds.append("intermediate")
        else:
            baseline_preds.append("advanced")

    # If we have test labels for baseline comparison
    baseline_acc = accuracy_score(
        le.inverse_transform(y_test),
        [_rules_predict(X_test[i]) for i in range(len(y_test))],
    )

    report = classification_report(
        y_test, y_pred, target_names=le.classes_, output_dict=True
    )

    metrics = {
        "accuracy": round(accuracy, 4),
        "f1_weighted": round(f1, 4),
        "auc_ovr": round(auc, 4),
        "cv_mean": round(float(cv_scores.mean()), 4),
        "cv_std": round(float(cv_scores.std()), 4),
        "baseline_accuracy": round(baseline_acc, 4),
        "improvement": round(accuracy - baseline_acc, 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "classification_report": report,
    }

    logger.info("=== Level Classifier Results ===")
    logger.info("Accuracy: %.4f (baseline: %.4f, +%.4f)", accuracy, baseline_acc, accuracy - baseline_acc)
    logger.info("F1 (weighted): %.4f", f1)
    logger.info("AUC (OVR): %.4f", auc)
    logger.info("CV: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())
    logger.info(
        "Report:\n%s",
        classification_report(y_test, y_pred, target_names=le.classes_),
    )

    # Feature importance
    importances = dict(zip(FEATURE_NAMES, model.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    logger.info("Feature importance:")
    for name, imp in sorted_imp:
        logger.info("  %-20s %.4f", name, imp)

    # Save model bundle
    bundle = {
        "model": model,
        "label_encoder": le,
        "feature_names": FEATURE_NAMES,
        "version": "1.0.0",
        "metrics": metrics,
        "feature_importance": importances,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, out)
    logger.info("Saved model to %s", out)

    return metrics


def _rules_predict(features: np.ndarray) -> str:
    """Rules-based prediction for baseline comparison."""
    attempts = features[0]  # total_attempts
    accuracy = features[2]  # accuracy
    if attempts < 5:
        return "beginner"
    elif accuracy < 0.5:
        return "beginner"
    elif accuracy < 0.75:
        return "intermediate"
    else:
        return "advanced"


def main():
    parser = argparse.ArgumentParser(description="Train level classifier")
    parser.add_argument("--data", default="data/training_data.csv")
    parser.add_argument("--output", default="models/level_classifier.joblib")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    metrics = train_level_classifier(args.data, args.output, args.test_size, args.seed)
    print(f"\n✅ Training complete. Metrics: {json.dumps({k: v for k, v in metrics.items() if k != 'classification_report'}, indent=2)}")


if __name__ == "__main__":
    main()
