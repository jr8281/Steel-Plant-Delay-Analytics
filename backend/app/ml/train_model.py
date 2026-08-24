"""
Train delay-duration risk classifier with time-series features.

Target: bucket the effective delay duration (eff_durn) into short/medium/long,
predicted from features known at the time a delay is logged (shop, equipment,
agency/cause, day of week, and time-series features like rolling failure rates).

Prevents label leakage by excluding duration-derived features.
"""
from datetime import datetime, timezone, timedelta

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.ml.model_store import save_artifacts
from app.models.models import Agency, DelayEvent, Equipment, Shop

logger = get_logger(__name__)

# Base categorical features (available before delay resolves)
BASE_FEATURE_COLUMNS = ["shop_code", "equipment_name", "agency_code", "day_of_week"]

# Time-series features (rolling statistics from historical data)
TIMESERIES_FEATURE_COLUMNS = [
    "equipment_failure_rate_7d",    # Failures in past 7 days / total delays
    "equipment_mttr_7d",             # Mean time to repair (past 7 days)
    "cause_frequency_7d",            # How often this cause occurred (past 7 days)
]

ALL_FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + TIMESERIES_FEATURE_COLUMNS
TARGET_COLUMN = "duration_bucket"
MIN_TRAINING_ROWS = 40


def _bucket_duration(hours: float) -> str:
    """Bucket delay duration into risk categories."""
    if hours < 2:
        return "short"
    if hours <= 6:
        return "medium"
    return "long"


def _compute_equipment_failure_rate(
    df: pd.DataFrame,
    equipment_name: str,
    delay_date: pd.Timestamp,
    lookback_days: int = 7,
) -> float:
    """
    Compute equipment failure rate in past N days.
    
    Represents: How many failures has this equipment had recently?
    Higher = more prone to failure = higher risk
    """
    cutoff_date = delay_date - timedelta(days=lookback_days)
    
    # Count delays for this equipment in lookback period
    recent_delays = df[
        (df["equipment_name"] == equipment_name) &
        (df["delay_date"] >= cutoff_date) &
        (df["delay_date"] < delay_date)
    ]
    
    # Avoid division by zero
    if len(recent_delays) == 0:
        return 0.0
    
    # Failure rate: distinct days with failures / total days in window
    failure_days = recent_delays["delay_date"].nunique()
    total_days = (delay_date - cutoff_date).days
    
    return min(float(failure_days / max(total_days, 1)), 1.0)


def _compute_equipment_mttr(
    df: pd.DataFrame,
    equipment_name: str,
    delay_date: pd.Timestamp,
    lookback_days: int = 7,
) -> float:
    """
    Compute mean time to repair (MTTR) for equipment in past N days.
    
    Represents: How long does this equipment take to repair on average?
    Higher MTTR = slower repairs = potentially longer delays
    """
    cutoff_date = delay_date - timedelta(days=lookback_days)
    
    recent_delays = df[
        (df["equipment_name"] == equipment_name) &
        (df["delay_date"] >= cutoff_date) &
        (df["delay_date"] < delay_date)
    ]
    
    if len(recent_delays) == 0:
        return 0.0
    
    return float(recent_delays["eff_durn"].mean())


def _compute_cause_frequency(
    df: pd.DataFrame,
    agency_code: str,
    delay_date: pd.Timestamp,
    lookback_days: int = 7,
) -> float:
    """
    Compute how frequently a cause occurred in past N days.
    
    Represents: Is this cause happening repeatedly?
    Higher frequency = systemic issue = higher risk
    """
    cutoff_date = delay_date - timedelta(days=lookback_days)
    
    recent_delays = df[
        (df["agency_code"] == agency_code) &
        (df["delay_date"] >= cutoff_date) &
        (df["delay_date"] < delay_date)
    ]
    
    return float(len(recent_delays))


def _load_training_frame(db: Session) -> pd.DataFrame:
    """Load training data with time-series features."""
    rows = (
        db.query(
            Shop.shop_code.label("shop_code"),
            Equipment.name.label("equipment_name"),
            Agency.code.label("agency_code"),
            DelayEvent.delay_date,
            DelayEvent.eff_durn,
        )
        .join(Shop, DelayEvent.shop_id == Shop.id)
        .outerjoin(Equipment, DelayEvent.equipment_id == Equipment.id)
        .join(Agency, DelayEvent.agency_id == Agency.id)
        .all()
    )
    
    df = pd.DataFrame(
        rows,
        columns=["shop_code", "equipment_name", "agency_code", "delay_date", "eff_durn"]
    )
    
    # Handle missing equipment names
    df["equipment_name"] = df["equipment_name"].fillna("UNKNOWN")
    
    # Convert delay_date to datetime
    df["delay_date"] = pd.to_datetime(df["delay_date"])
    
    # Sort by date for time-series feature computation
    df = df.sort_values("delay_date").reset_index(drop=True)
    
    # Extract day of week
    df["day_of_week"] = df["delay_date"].dt.day_name()
    
    # Compute time-series features
    logger.info("Computing time-series features...")
    
    df["equipment_failure_rate_7d"] = df.apply(
        lambda row: _compute_equipment_failure_rate(df, row["equipment_name"], row["delay_date"]),
        axis=1
    )
    
    df["equipment_mttr_7d"] = df.apply(
        lambda row: _compute_equipment_mttr(df, row["equipment_name"], row["delay_date"]),
        axis=1
    )
    
    df["cause_frequency_7d"] = df.apply(
        lambda row: _compute_cause_frequency(df, row["agency_code"], row["delay_date"]),
        axis=1
    )
    
    # Create target variable
    df[TARGET_COLUMN] = df["eff_durn"].apply(_bucket_duration)
    
    logger.info(f"Loaded {len(df)} training records with time-series features")
    
    return df


def train(db: Session) -> dict:
    """
    Train Random Forest classifier with time-series features.
    
    Returns:
        Dictionary with metrics: accuracy, f1, class_distribution, feature_importance
    """
    df = _load_training_frame(db)
    
    if len(df) < MIN_TRAINING_ROWS:
        raise ValueError(
            f"Not enough data to train reliably: {len(df)} rows available, "
            f"minimum {MIN_TRAINING_ROWS} required."
        )
    
    X = df[ALL_FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    # Split data: 80% train, 20% test (stratified by target)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None
    )
    
    logger.info(f"Train set: {len(X_train)}, Test set: {len(X_test)}")
    
    # Build pipeline: one-hot encode categoricals, then train Random Forest
    categorical_features = ["shop_code", "equipment_name", "agency_code", "day_of_week"]
    numerical_features = TIMESERIES_FEATURE_COLUMNS
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
            ("num", "passthrough", numerical_features),
        ]
    )
    
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            verbose=1
        ))
    ])
    
    # Train
    logger.info("Training Random Forest model with time-series features...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    
    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    # Feature importance (only for tree-based features)
    feature_importance = pipeline.named_steps["classifier"].feature_importances_
    
    # Get feature names after preprocessing
    feature_names = (
        list(pipeline.named_steps["preprocessor"]
             .named_transformers_["cat"]
             .get_feature_names_out(categorical_features)) +
        numerical_features
    )
    
    # Top time-series features
    importance_dict = dict(zip(feature_names, feature_importance))
    top_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
    
    metrics = {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "class_distribution": {
            "short": int(y_train[y_train == "short"].count()),
            "medium": int(y_train[y_train == "medium"].count()),
            "long": int(y_train[y_train == "long"].count()),
        },
        "classification_report": report,
        "top_features": [{"name": name, "importance": float(imp)} for name, imp in top_features],
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Save model artifacts
    save_artifacts(pipeline, metrics)
    
    logger.info(
        f"Training complete. Accuracy: {accuracy:.4f}, Macro F1: {macro_f1:.4f}"
    )
    
    return metrics


if __name__ == "__main__":
    """Standalone training script."""
    from app.core.database import get_db_session
    
    db = next(get_db_session())
    metrics = train(db)
    print("Training metrics:", metrics)