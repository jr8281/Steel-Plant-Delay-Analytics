"""Serves predictions from the trained delay-risk model."""
import pandas as pd

from app.ml.model_store import is_trained, load_metrics, load_model
from app.ml.train_model import FEATURE_COLUMNS


class ModelNotTrainedError(Exception):
    pass


def predict_delay_bucket(shop_code: str, equipment_name: str | None, agency_code: str, day_of_week: str) -> dict:
    if not is_trained():
        raise ModelNotTrainedError("No trained model is available yet. Train the model first.")

    model = load_model()
    row = pd.DataFrame(
        [{
            "shop_code": shop_code,
            "equipment_name": equipment_name or "UNKNOWN",
            "agency_code": agency_code,
            "day_of_week": day_of_week,
        }],
        columns=FEATURE_COLUMNS,
    )
    predicted_class = model.predict(row)[0]
    probabilities = dict(zip(model.classes_, model.predict_proba(row)[0].round(4)))
    return {
        "predicted_bucket": predicted_class,
        "confidence": float(probabilities[predicted_class]),
        "probabilities": {k: float(v) for k, v in probabilities.items()},
    }


def get_model_info() -> dict:
    if not is_trained():
        return {"trained": False}
    metrics = load_metrics()
    return {"trained": True, **(metrics or {})}
