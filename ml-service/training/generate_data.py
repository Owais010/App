"""
Synthetic Data Generator — Produce realistic training data.

Generates user-topic feature vectors with known ground-truth labels
for training level classifiers and difficulty recommenders.

The generated data models realistic learner behavior patterns:
  - Beginners: low accuracy, slow, few attempts
  - Intermediate: moderate accuracy, medium speed, building streaks
  - Advanced: high accuracy, fast, many attempts, strong hard-question perf

Usage:
    python -m training.generate_data --rows 10000 --output data/training_data.csv
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LEARNER ARCHETYPES
# ─────────────────────────────────────────────────────────────────────────────

ARCHETYPES = {
    "beginner": {
        "weight": 0.35,
        "accuracy": (0.15, 0.48),
        "attempts": (1, 20),
        "weighted_score": (0.0, 3.0),
        "recent_accuracy": (0.1, 0.5),
        "trend": (-0.15, 0.10),
        "streak": (0, 3),
        "avg_time": (15, 60),
        "days_since": (0, 90),
        "easy_acc": (0.3, 0.7),
        "medium_acc": (0.1, 0.4),
        "hard_acc": (0.0, 0.2),
        "global_acc": (0.15, 0.45),
        "topics_attempted": (1, 5),
    },
    "intermediate": {
        "weight": 0.40,
        "accuracy": (0.45, 0.74),
        "attempts": (8, 60),
        "weighted_score": (2.0, 12.0),
        "recent_accuracy": (0.4, 0.8),
        "trend": (-0.05, 0.15),
        "streak": (0, 8),
        "avg_time": (8, 35),
        "days_since": (0, 45),
        "easy_acc": (0.6, 0.95),
        "medium_acc": (0.4, 0.75),
        "hard_acc": (0.1, 0.45),
        "global_acc": (0.4, 0.7),
        "topics_attempted": (3, 15),
    },
    "advanced": {
        "weight": 0.25,
        "accuracy": (0.72, 0.98),
        "attempts": (15, 150),
        "weighted_score": (8.0, 40.0),
        "recent_accuracy": (0.7, 1.0),
        "trend": (-0.05, 0.10),
        "streak": (2, 20),
        "avg_time": (5, 20),
        "days_since": (0, 30),
        "easy_acc": (0.85, 1.0),
        "medium_acc": (0.7, 0.95),
        "hard_acc": (0.45, 0.9),
        "global_acc": (0.65, 0.92),
        "topics_attempted": (5, 25),
    },
}


def _sample_uniform(low: float, high: float) -> float:
    """Sample uniformly in [low, high]."""
    return random.uniform(low, high)


def _sample_int(low: int, high: int) -> int:
    return random.randint(low, high)


def generate_row(archetype: str) -> dict:
    """Generate one training row for a given archetype."""
    cfg = ARCHETYPES[archetype]

    accuracy = _sample_uniform(*cfg["accuracy"])
    attempts = _sample_int(*cfg["attempts"])
    correct = int(round(accuracy * attempts))
    correct = min(correct, attempts)

    # Add noise (±5% of accuracy)
    noise = random.gauss(0, 0.03)

    row = {
        "total_attempts": attempts,
        "correct_attempts": correct,
        "accuracy": round(min(max(accuracy + noise, 0), 1), 4),
        "weighted_score": round(_sample_uniform(*cfg["weighted_score"]), 4),
        "recent_accuracy": round(
            min(max(_sample_uniform(*cfg["recent_accuracy"]) + noise, 0), 1), 4
        ),
        "accuracy_trend": round(_sample_uniform(*cfg["trend"]), 4),
        "streak_length": _sample_int(*cfg["streak"]),
        "avg_time_per_q": round(_sample_uniform(*cfg["avg_time"]), 2),
        "days_since_last": round(_sample_uniform(*cfg["days_since"]), 2),
        "easy_accuracy": round(
            min(max(_sample_uniform(*cfg["easy_acc"]) + noise, 0), 1), 4
        ),
        "medium_accuracy": round(
            min(max(_sample_uniform(*cfg["medium_acc"]) + noise, 0), 1), 4
        ),
        "hard_accuracy": round(
            min(max(_sample_uniform(*cfg["hard_acc"]) + noise, 0), 1), 4
        ),
        "global_accuracy": round(
            min(max(_sample_uniform(*cfg["global_acc"]) + noise, 0), 1), 4
        ),
        "topics_attempted": _sample_int(*cfg["topics_attempted"]),
        # Labels
        "level": archetype,
        "optimal_difficulty": _optimal_difficulty(archetype, accuracy),
    }

    return row


def _optimal_difficulty(level: str, accuracy: float) -> str:
    """
    Determine optimal difficulty targeting ~70% success rate.

    Zone of Proximal Development:
      - If accuracy at current level is >80%, push harder
      - If accuracy at current level is <50%, pull back
    """
    if level == "beginner":
        if accuracy > 0.6:
            return "medium"
        return "easy"
    elif level == "intermediate":
        if accuracy > 0.8:
            return "hard"
        elif accuracy < 0.5:
            return "easy"
        return "medium"
    else:  # advanced
        if accuracy < 0.6:
            return "medium"
        return "hard"


def generate_dataset(n_rows: int, seed: int = 42) -> pd.DataFrame:
    """Generate a full synthetic dataset with realistic distributions."""
    random.seed(seed)
    np.random.seed(seed)

    rows = []
    weights = [ARCHETYPES[a]["weight"] for a in ARCHETYPES]
    archetypes = list(ARCHETYPES.keys())

    for _ in range(n_rows):
        arch = random.choices(archetypes, weights=weights, k=1)[0]
        rows.append(generate_row(arch))

    df = pd.DataFrame(rows)

    # Add some edge cases
    # Cold-start users (very few attempts)
    for _ in range(int(n_rows * 0.05)):
        row = generate_row("beginner")
        row["total_attempts"] = random.randint(0, 3)
        row["correct_attempts"] = random.randint(0, row["total_attempts"])
        row["accuracy"] = (
            row["correct_attempts"] / max(row["total_attempts"], 1)
        )
        row["recent_accuracy"] = row["accuracy"]
        row["streak_length"] = row["correct_attempts"]
        rows.append(row)

    # Returning power users
    for _ in range(int(n_rows * 0.03)):
        row = generate_row("advanced")
        row["days_since_last"] = random.uniform(60, 365)
        row["recent_accuracy"] = max(
            row["accuracy"] - random.uniform(0.1, 0.3), 0
        )
        row["accuracy_trend"] = round(
            row["recent_accuracy"] - row["accuracy"], 4
        )
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    logger.info(
        "Generated %d rows: %s",
        len(df),
        df["level"].value_counts().to_dict(),
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ML training data")
    parser.add_argument("--rows", type=int, default=10000, help="Number of rows")
    parser.add_argument(
        "--output",
        type=str,
        default="data/training_data.csv",
        help="Output CSV path",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    df = generate_dataset(args.rows, args.seed)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    print(f"Level distribution:\n{df['level'].value_counts()}")
    print(f"Difficulty distribution:\n{df['optimal_difficulty'].value_counts()}")


if __name__ == "__main__":
    main()
