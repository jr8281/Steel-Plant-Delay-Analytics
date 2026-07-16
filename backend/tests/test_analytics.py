from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import Agency, DelayEvent, Equipment, Shop, User
from app.routers.delays import update_delay
from app.schemas.schemas import DelayEventUpdate
from app.services import analytics_engine as analytics


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    first_shop = Shop(shop_code="01", name="CHP")
    second_shop = Shop(shop_code="02", name="SMS")
    equipment = Equipment(name="Conveyor")
    operating = Agency(code="O")
    electrical = Agency(code="E")
    session.add_all([first_shop, second_shop, equipment, operating, electrical])
    session.flush()
    session.add_all([
        DelayEvent(delay_date=date(2026, 1, 1), shop_id=first_shop.id, equipment_id=equipment.id, agency_id=operating.id, durn=3, eff_durn=2, cum_delay=2, freq=1),
        DelayEvent(delay_date=date(2026, 1, 2), shop_id=first_shop.id, equipment_id=equipment.id, agency_id=electrical.id, durn=5, eff_durn=4, cum_delay=6, freq=1),
        DelayEvent(delay_date=date(2026, 1, 2), shop_id=second_shop.id, equipment_id=equipment.id, agency_id=operating.id, durn=8, eff_durn=10, cum_delay=10, freq=1),
    ])
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_overview_returns_eff_durn_kpis(db):
    result = analytics.overview(db, User(role="admin"))
    assert result["total_delay_hours"] == pytest.approx(16.0)
    assert result["total_delay_events"] == 3
    assert result["avg_delay_hours"] == pytest.approx(5.33)
    assert result["worst_shop"] == "SMS"
    assert result["worst_equipment"] == "Conveyor"
    assert result["most_frequent_cause"] == "O"


def test_pareto_sums_to_100_percent(db):
    result = analytics.pareto_by_cause(db, User(role="admin"))
    assert result[-1]["cum_pct"] == pytest.approx(100.0)


def test_shop_user_is_scoped_to_assigned_shop(db):
    shop = db.query(Shop).filter_by(shop_code="01").one()
    operator = User(role="operator", shop_id=shop.id)
    summary = analytics.overview(db, operator)
    comparison = analytics.compare_shops(db, operator, [shop.id, shop.id + 1], "eff_durn", None, None)
    assert summary["total_delay_events"] == 2
    assert {row["shop"] for row in comparison} == {"CHP"}


def test_manager_can_persist_delay_edit(db):
    event = db.query(DelayEvent).first()
    update_delay(event.id, DelayEventUpdate(descr="Corrected delay description"), db, User(role="admin"))
    assert db.get(DelayEvent, event.id).descr == "Corrected delay description"
