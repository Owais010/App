# Models Directory

This directory contains trained model files:

- `skill_gap_model.pkl` - Skill Gap Regression Model (GradientBoostingRegressor)
- `difficulty_model.pkl` - Difficulty Classification Model (RandomForestClassifier)
- `ranking_model.pkl` - Ranking Scoring Model (GradientBoostingRegressor)

## Generating Models

Run the training pipeline to generate models:

```bash
cd ml-service
python training/train_all.py
```

This will:

1. Generate synthetic training data
2. Train all three models
3. Save model files to this directory
