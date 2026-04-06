"""Load XGBoost fraud model and produce calibrated cheating probability."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

import joblib
import numpy as np

logger = logging.getLogger(__name__)

_model: Optional[Any] = None
_MODEL_FILENAME = "xgboost_model.pkl"


def model_path() -> Path:
    return Path(__file__).resolve().parent.parent / "models" / _MODEL_FILENAME


def load_fraud_model():
    global _model
    if _model is not None:
        return _model
    path = model_path()
    if not path.is_file():
        logger.warning("Fraud model not found at %s — ML fraud scoring disabled", path)
        return None
    try:
        _model = joblib.load(path)
        logger.info("Loaded fraud model from %s", path)
    except Exception as e:
        logger.exception("Failed to load fraud model: %s", e)
        _model = None
    return _model


def predict_fraud_probability(features_row: List[float]) -> float:
    """
    features_row order must match training CSV:
    score, time_taken, attempts, avg_user_score, tasks_completed_today,
    account_age_days, previous_rewards, time_of_day
    """
    model = load_fraud_model()
    if model is None:
        return 0.25

    x = np.array([features_row], dtype=np.float32)
    try:
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(x)[0]
            # binary: column 1 = positive class fraud
            return float(proba[1] if len(proba) > 1 else proba[0])
        pred = model.predict(x)[0]
        return float(pred)
    except Exception as e:
        logger.exception("Fraud predict error: %s", e)
        return 0.5


def blend_with_similarity(ml_prob: float, task_similarity: float, weight_ml: float = 0.65) -> float:
    """Combine model output with semantic alignment (1 - similarity ~ mismatch)."""
    mismatch = max(0.0, min(1.0, 1.0 - task_similarity))
    combined = weight_ml * ml_prob + (1.0 - weight_ml) * mismatch
    return max(0.0, min(1.0, float(combined)))
