import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import IngestionLog
from app.services.ingestion import ingest_dataframe


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def _sample_df():
    return pd.DataFrame(
        [
            {
                "Delay Date": pd.Timestamp("2026-01-01"),
                "Shop Code": "01",
                "Shop": "CHP",
                "Eqpt": "STKR",
                "agency": "O",
                "Durn": 2.0,
                "Eff Durn": 2.0,
            }
        ]
    )


def test_ingestion_writes_audit_log(db):
    count = ingest_dataframe(
        _sample_df(), db, replace_existing=True, filename="test.csv", uploaded_by_id=None
    )
    assert count == 1

    log = db.query(IngestionLog).first()
    assert log is not None
    assert log.filename == "test.csv"
    assert log.mode == "replace"
    assert log.records_ingested == 1


def test_append_mode_does_not_delete_existing_rows(db):
    ingest_dataframe(_sample_df(), db, replace_existing=True, filename="first.csv")
    ingest_dataframe(_sample_df(), db, replace_existing=False, filename="second.csv")

    logs = db.query(IngestionLog).order_by(IngestionLog.id).all()
    assert [entry.mode for entry in logs] == ["replace", "append"]
