from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.ml.model_store import is_trained
from app.ml.train_model import train
from app.models.models import Agency, DelayEvent, Equipment, Shop
from app.services.ml_engine import ModelNotTrainedError, predict_delay_bucket


@pytest.fixture()
def db(tmp_path, monkeypatch):
    import app.ml.model_store as model_store

    monkeypatch.setattr(model_store, "ARTIFACT_DIR", tmp_path)
    monkeypatch.setattr(model_store, "MODEL_PATH", tmp_path / "model.joblib")
    monkeypatch.setattr(model_store, "METRICS_PATH", tmp_path / "metrics.json")
    monkeypatch.setattr(model_store, "_model_cache", None)
    monkeypatch.setattr(model_store, "_metrics_cache", None)

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    shop = Shop(shop_code="01", name="CHP")
    equipment = Equipment(name="Conveyor")
    operating = Agency(code="O")
    electrical = Agency(code="E")
    session.add_all([shop, equipment, operating, electrical])
    session.flush()

    base_date = date(2026, 1, 1)
    for i in range(60):
        agency = operating if i % 2 == 0 else electrical
        duration = 1.0 if i % 3 == 0 else (4.0 if i % 3 == 1 else 8.0)
        session.add(
            DelayEvent(
                delay_date=base_date + timedelta(days=i % 7),
                shop_id=shop.id,
                equipment_id=equipment.id,
                agency_id=agency.id,
                durn=duration,
                eff_durn=duration,
                cum_delay=duration,
                freq=1,
            )
        )
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_predict_fails_before_training(db):
    with pytest.raises(ModelNotTrainedError):
        predict_delay_bucket(
            shop_code="01", equipment_name="Conveyor", agency_code="O", day_of_week="Monday"
        )


def test_train_produces_metrics_and_model(db):
    metrics = train(db)
    assert is_trained()
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert metrics["n_samples"] == 60
    assert metrics["n_train"] + metrics["n_test"] == 60


def test_predict_after_training_returns_valid_bucket(db):
    train(db)
    result = predict_delay_bucket(
        shop_code="01", equipment_name="Conveyor", agency_code="O", day_of_week="Monday"
    )
    assert result["predicted_bucket"] in {"short", "medium", "long"}
    assert 0.0 <= result["confidence"] <= 1.0
    assert abs(sum(result["probabilities"].values()) - 1.0) < 0.01
