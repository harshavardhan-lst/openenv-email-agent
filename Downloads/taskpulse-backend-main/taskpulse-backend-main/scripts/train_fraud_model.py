"""
Train XGBoost fraud classifier from datasets/fraud_dataset.csv
and write backend/models/xgboost_model.pkl.

Feature order (must match inference in backend):
score, time_taken, attempts, avg_user_score, tasks_completed_today,
account_age_days, previous_rewards, time_of_day
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "datasets" / "fraud_dataset.csv"
OUT_PATH = ROOT / "backend" / "models" / "xgboost_model.pkl"


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"Missing dataset: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    X = df.drop("fraud", axis=1)
    y = df["fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pos = float(y_train.sum())
    neg = float(len(y_train) - pos)
    scale = (neg / pos) if pos > 0 else 1.0

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    print("Confusion Matrix:\n", confusion_matrix(y_test, predictions))
    print("\nClassification Report:\n", classification_report(y_test, predictions))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT_PATH)
    print(f"\nSaved model to {OUT_PATH}")


if __name__ == "__main__":
    main()
