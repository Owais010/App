"""
Train All Models — Single entry point for the complete training pipeline.

Steps:
  1. Generate synthetic training data (if not exists)
  2. Train level classifier (XGBoost)
  3. Train difficulty recommender (LightGBM)
  4. Print combined metrics report

Usage:
    python -m training.train_all
    python -m training.train_all --rows 50000 --force-regen
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def train_all(
    n_rows: int = 10000,
    force_regen: bool = False,
    data_path: str = "data/training_data.csv",
    seed: int = 42,
) -> dict:
    """Run the complete training pipeline."""
    from training.generate_data import generate_dataset
    from training.train_level_classifier import train_level_classifier
    from training.train_difficulty_recommender import train_difficulty_recommender

    results = {}

    # ── Step 1: Generate data ────────────────────────────────────────────────
    data_file = Path(data_path)
    if force_regen or not data_file.exists():
        logger.info("Generating %d rows of synthetic training data...", n_rows)
        df = generate_dataset(n_rows, seed)
        data_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(data_file, index=False)
        logger.info("Saved training data to %s", data_file)
    else:
        logger.info("Using existing training data at %s", data_file)

    # ── Step 2: Train level classifier ───────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING: Level Classifier (XGBoost)")
    logger.info("=" * 60)
    results["level_classifier"] = train_level_classifier(
        data_path=str(data_file),
        output_path="models/level_classifier.joblib",
        random_state=seed,
    )

    # ── Step 3: Train difficulty recommender ─────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING: Difficulty Recommender (LightGBM)")
    logger.info("=" * 60)
    results["difficulty_recommender"] = train_difficulty_recommender(
        data_path=str(data_file),
        output_path="models/difficulty_recommender.joblib",
        random_state=seed,
    )

    # ── Summary ──────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING PIPELINE COMPLETE")
    logger.info("=" * 60)

    for model_name, metrics in results.items():
        acc = metrics.get("accuracy", 0)
        baseline = metrics.get("baseline_accuracy", 0)
        improvement = metrics.get("improvement", 0)
        logger.info(
            "  %-30s acc=%.4f  baseline=%.4f  improvement=+%.4f",
            model_name,
            acc,
            baseline,
            improvement,
        )

    return results


def main():
    parser = argparse.ArgumentParser(description="Train all ML models")
    parser.add_argument("--rows", type=int, default=10000, help="Training data rows")
    parser.add_argument("--force-regen", action="store_true", help="Regenerate data")
    parser.add_argument("--data", default="data/training_data.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    results = train_all(args.rows, args.force_regen, args.data, args.seed)

    # Print JSON summary
    summary = {
        k: {kk: vv for kk, vv in v.items() if kk != "classification_report"}
        for k, v in results.items()
    }
    print(f"\n📊 Results:\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
