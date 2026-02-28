"""
Synthetic Data Generator for Training.

Generates realistic training data for the Adaptive Learning Intelligence Engine.
This script creates a CSV file with the required input schema.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np


def generate_training_data(n_samples: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic training data with realistic distributions.
    
    Args:
        n_samples: Number of samples to generate.
        random_seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with training data.
    """
    np.random.seed(random_seed)
    
    # Generate base features with realistic distributions
    data = {
        "user_id": [f"user_{i:05d}" for i in range(n_samples)],
        "topic_id": [f"topic_{np.random.randint(1, 101):03d}" for _ in range(n_samples)],
        
        # Attempt count: typically 1-50, skewed towards lower values
        "attempt_count": np.maximum(1, np.random.exponential(10, n_samples).astype(int)),
        
        # Average response time in seconds: 5-180 seconds
        "avg_response_time": np.clip(np.random.gamma(5, 10, n_samples), 5, 180),
        
        # Self confidence rating: 0-1, beta distribution
        "self_confidence_rating": np.clip(np.random.beta(4, 3, n_samples), 0, 1),
        
        # Difficulty feedback: 1-5, discrete
        "difficulty_feedback": np.random.randint(1, 6, n_samples),
        
        # Session duration in minutes: 5-120 minutes
        "session_duration": np.clip(np.random.gamma(10, 5, n_samples), 5, 120),
        
        # Previous mastery score: 0-1, beta distribution
        "previous_mastery_score": np.clip(np.random.beta(3, 2, n_samples), 0, 1),
        
        # Time since last attempt in hours: 0-720 hours (30 days)
        "time_since_last_attempt": np.clip(np.random.exponential(48, n_samples), 0, 720)
    }
    
    # Generate correct attempts based on attempt count
    # Use a varying success rate for different learners
    success_rates = np.random.beta(3, 2, n_samples)  # Varying per learner
    data["correct_attempts"] = np.minimum(
        data["attempt_count"],
        np.random.binomial(data["attempt_count"], success_rates)
    )
    
    # Ensure correct_attempts doesn't exceed attempt_count
    data["correct_attempts"] = np.minimum(data["correct_attempts"], data["attempt_count"])
    
    df = pd.DataFrame(data)
    
    # Reorder columns
    column_order = [
        "user_id", "topic_id", "attempt_count", "correct_attempts",
        "avg_response_time", "self_confidence_rating", "difficulty_feedback",
        "session_duration", "previous_mastery_score", "time_since_last_attempt"
    ]
    df = df[column_order]
    
    return df


def print_data_statistics(df: pd.DataFrame) -> None:
    """Print statistics about the generated data."""
    print("\n" + "="*60)
    print("GENERATED DATA STATISTICS")
    print("="*60)
    
    print(f"\nTotal samples: {len(df)}")
    print(f"\nUnique users: {df['user_id'].nunique()}")
    print(f"Unique topics: {df['topic_id'].nunique()}")
    
    print("\n" + "-"*40)
    print("Numeric Column Statistics:")
    print("-"*40)
    
    numeric_cols = [
        "attempt_count", "correct_attempts", "avg_response_time",
        "self_confidence_rating", "difficulty_feedback", "session_duration",
        "previous_mastery_score", "time_since_last_attempt"
    ]
    
    for col in numeric_cols:
        print(f"\n{col}:")
        print(f"  Min: {df[col].min():.2f}")
        print(f"  Max: {df[col].max():.2f}")
        print(f"  Mean: {df[col].mean():.2f}")
        print(f"  Std: {df[col].std():.2f}")
    
    # Compute and show accuracy distribution
    accuracy = df["correct_attempts"] / df["attempt_count"]
    print(f"\nDerived accuracy_rate:")
    print(f"  Min: {accuracy.min():.2f}")
    print(f"  Max: {accuracy.max():.2f}")
    print(f"  Mean: {accuracy.mean():.2f}")
    print(f"  Std: {accuracy.std():.2f}")
    
    # Show difficulty distribution based on accuracy
    easy = (accuracy > 0.8).sum()
    medium = ((accuracy >= 0.5) & (accuracy <= 0.8)).sum()
    hard = (accuracy < 0.5).sum()
    
    print(f"\nExpected difficulty distribution:")
    print(f"  Easy (accuracy > 0.8): {easy} ({100*easy/len(df):.1f}%)")
    print(f"  Medium (0.5 <= accuracy <= 0.8): {medium} ({100*medium/len(df):.1f}%)")
    print(f"  Hard (accuracy < 0.5): {hard} ({100*hard/len(df):.1f}%)")


def main():
    """Generate and save training data."""
    print("="*60)
    print("SYNTHETIC DATA GENERATOR")
    print("="*60)
    
    # Parse command line arguments
    n_samples = 5000
    if len(sys.argv) > 1:
        try:
            n_samples = int(sys.argv[1])
        except ValueError:
            print(f"Invalid sample count: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"\nGenerating {n_samples} samples...")
    
    # Generate data
    df = generate_training_data(n_samples=n_samples)
    
    # Print statistics
    print_data_statistics(df)
    
    # Save to CSV
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = data_dir / "training_data.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n" + "="*60)
    print(f"Data saved to: {output_path}")
    print("="*60)
    
    # Show sample rows
    print("\nSample rows:")
    print(df.head(5).to_string())


if __name__ == "__main__":
    main()
