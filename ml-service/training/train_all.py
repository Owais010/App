"""
Master training script that runs all training pipelines.

This script:
1. Generates synthetic training data
2. Trains the Skill Gap model
3. Trains the Difficulty model
4. Trains the Ranking model
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import subprocess


def run_script(script_name: str, args: list = None) -> bool:
    """
    Run a Python script as a subprocess.
    
    Args:
        script_name: Name of the script to run.
        args: Optional list of arguments.
        
    Returns:
        True if successful, False otherwise.
    """
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60 + "\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def main():
    """Run complete training pipeline."""
    print("="*60)
    print("ADAPTIVE LEARNING INTELLIGENCE ENGINE")
    print("COMPLETE TRAINING PIPELINE")
    print("="*60)
    
    # Step 1: Generate training data
    print("\n[1/4] Generating training data...")
    if not run_script("generate_data.py", ["5000"]):
        print("ERROR: Data generation failed!")
        sys.exit(1)
    
    # Step 2: Train Skill Gap model
    print("\n[2/4] Training Skill Gap model...")
    if not run_script("train_skill_gap.py"):
        print("ERROR: Skill Gap model training failed!")
        sys.exit(1)
    
    # Step 3: Train Difficulty model
    print("\n[3/4] Training Difficulty model...")
    if not run_script("train_difficulty.py"):
        print("ERROR: Difficulty model training failed!")
        sys.exit(1)
    
    # Step 4: Train Ranking model
    print("\n[4/4] Training Ranking model...")
    if not run_script("train_ranking.py"):
        print("ERROR: Ranking model training failed!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("ALL TRAINING COMPLETE!")
    print("="*60)
    print("\nModels saved in: ml-service/models/")
    print("  - skill_gap_model.pkl")
    print("  - difficulty_model.pkl")
    print("  - ranking_model.pkl")
    print("\nYou can now start the service with:")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
