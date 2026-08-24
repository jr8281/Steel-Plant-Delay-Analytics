"""Loads and caches the trained delay-risk model and its evaluation metrics."""
import json
from pathlib import Path

import joblib

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "delay_risk_model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"

_model_cache = None
_metrics_cache = None


def save_artifacts(model, metrics: dict) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    global _model_cache, _metrics_cache
    _model_cache = model
    _metrics_cache = metrics


def load_model():
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            return None
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def load_metrics() -> dict | None:
    global _metrics_cache
    if _metrics_cache is None:
        if not METRICS_PATH.exists():
            return None
        _metrics_cache = json.loads(METRICS_PATH.read_text())
    return _metrics_cache


def is_trained() -> bool:
    return MODEL_PATH.exists() and METRICS_PATH.exists()
