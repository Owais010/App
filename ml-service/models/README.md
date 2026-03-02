# ML Models

Trained models are stored here in joblib format.

## Files

- `level_classifier.joblib` — XGBoost multiclass (beginner/intermediate/advanced)
- `difficulty_recommender.joblib` — LightGBM multiclass (easy/medium/hard)

## Training

```bash
cd ml-service
python -m training.train_all --rows 10000
```

Models are bundled as dicts containing:

- `model` — trained sklearn/xgboost/lightgbm estimator
- `label_encoder` — LabelEncoder for target classes
- `feature_names` — list of 14 feature names in canonical order
- `version` — semantic version string
- `metrics` — training metrics (accuracy, f1, auc, etc.)
- `feature_importance` — dict of feature_name → importance score
