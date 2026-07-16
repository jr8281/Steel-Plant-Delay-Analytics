from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import Agency, DelayEvent, Equipment, Shop, User
from app.schemas.schemas import DelayEventUpdate

router = APIRouter(tags=["delay events"])


def _visible_query(db: Session, user: User):
    query = db.query(DelayEvent).options(joinedload(DelayEvent.shop), joinedload(DelayEvent.equipment), joinedload(DelayEvent.agency))
    return query


def _serialize(event: DelayEvent) -> dict:
    return {"id": event.id, "delay_date": event.delay_date.isoformat(), "shop_code": event.shop.shop_code, "shop": event.shop.name, "equipment_name": event.equipment.name if event.equipment else None, "agency_code": event.agency.code, "sub_eqpt": event.sub_eqpt, "from_time": event.from_time, "upto_time": event.upto_time, "durn": event.durn, "eff_durn": event.eff_durn, "cum_delay": event.cum_delay, "freq": event.freq, "descr": event.descr, "material": event.material, "delay_code": event.delay_code, "contd": event.contd}


@router.get("/shops")
def shops(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Shop)
    return [{"id": item.id, "shop_code": item.shop_code, "name": item.name} for item in query.order_by(Shop.name)]


@router.get("/filters")
def filters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    events = _visible_query(db, user).all()
    return {"equipment": sorted({e.equipment.name for e in events if e.equipment}), "causes": sorted({e.agency.code for e in events}), "date_min": min((e.delay_date for e in events), default=None), "date_max": max((e.delay_date for e in events), default=None)}


@router.get("/delays")
def list_delays(shop_ids: list[int] | None = Query(None), equipment: str | None = None, cause: str | None = None, start_date: date | None = None, end_date: date | None = None, limit: int = Query(1000, le=5000), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = _visible_query(db, user)
    if shop_ids:
        query = query.filter(DelayEvent.shop_id.in_(shop_ids))
    if equipment:
        query = query.join(Equipment).filter(Equipment.name == equipment)
    if cause:
        query = query.join(Agency).filter(Agency.code == cause)
    if start_date:
        query = query.filter(DelayEvent.delay_date >= start_date)
    if end_date:
        query = query.filter(DelayEvent.delay_date <= end_date)
    rows = query.order_by(DelayEvent.delay_date.desc(), DelayEvent.id.desc()).limit(limit).all()
    return {"total": len(rows), "items": [_serialize(row) for row in rows]}


@router.patch("/delays/{delay_id}")
def update_delay(delay_id: int, payload: DelayEventUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    event = db.get(DelayEvent, delay_id)
    if not event:
        raise HTTPException(404, "Delay event not found")
    data = payload.model_dump(exclude_unset=True)
    if "shop_code" in data:
        shop = db.query(Shop).filter_by(shop_code=data.pop("shop_code")).first()
        if not shop:
            raise HTTPException(422, "Unknown shop code")
        event.shop_id = shop.id
    if "agency_code" in data:
        code = data.pop("agency_code")
        agency = db.query(Agency).filter_by(code=code).first() or Agency(code=code)
        db.add(agency); db.flush(); event.agency_id = agency.id
    if "equipment_name" in data:
        name = data.pop("equipment_name")
        if name:
            equipment = db.query(Equipment).filter_by(name=name).first() or Equipment(name=name)
            db.add(equipment); db.flush(); event.equipment_id = equipment.id
        else:
            event.equipment_id = None
    for field, value in data.items():
        setattr(event, field, value)
    db.commit(); db.refresh(event)
    return _serialize(event)
