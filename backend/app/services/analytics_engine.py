from datetime import date

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Agency, DelayEvent, Equipment, Shop


def _scope(query, user):
    return query


def overview(db: Session, user) -> dict:
    query = _scope(db.query(DelayEvent), user)
    total_hours, events = query.with_entities(func.coalesce(func.sum(DelayEvent.eff_durn), 0), func.count(DelayEvent.id)).one()
    total_hours = float(total_hours or 0)
    worst_shop = _scope(db.query(Shop.name, func.sum(DelayEvent.eff_durn).label("hours")).join(DelayEvent), user).group_by(Shop.name).order_by(func.sum(DelayEvent.eff_durn).desc()).first()
    worst_equipment = _scope(db.query(Equipment.name, func.sum(DelayEvent.eff_durn).label("hours")).join(DelayEvent), user).group_by(Equipment.name).order_by(func.sum(DelayEvent.eff_durn).desc()).first()
    top_cause = _scope(db.query(Agency.code, func.sum(DelayEvent.eff_durn).label("hours")).join(DelayEvent), user).group_by(Agency.code).order_by(func.sum(DelayEvent.eff_durn).desc()).first()
    most_frequent_cause = _scope(db.query(Agency.code, func.count(DelayEvent.id).label("events")).join(DelayEvent), user).group_by(Agency.code).order_by(func.count(DelayEvent.id).desc()).first()
    return {
        "total_delay_hours": round(total_hours, 2),
        "total_delay_events": events,
        "avg_delay_hours": round(total_hours / events, 2) if events else 0,
        "worst_shop": worst_shop[0] if worst_shop else "—",
        "worst_equipment": worst_equipment[0] if worst_equipment else "—",
        "most_frequent_cause": most_frequent_cause[0] if most_frequent_cause else "—",
        "top_cause": top_cause[0] if top_cause else "—",
    }


def shop_breakdown(db: Session, user) -> list[dict]:
    query = _scope(db.query(Shop.name.label("shop"), func.sum(DelayEvent.eff_durn).label("total_hours")).join(DelayEvent), user)
    return [{"shop": row.shop, "total_hours": round(float(row.total_hours), 2)} for row in query.group_by(Shop.name).order_by(func.sum(DelayEvent.eff_durn).desc()).all()]


def pareto_by_cause(db: Session, user) -> list[dict]:
    query = _scope(db.query(Agency.code.label("cause"), func.sum(DelayEvent.eff_durn).label("total_hours")).join(DelayEvent), user)
    rows = query.group_by(Agency.code).order_by(func.sum(DelayEvent.eff_durn).desc()).all()
    total = sum(float(row.total_hours) for row in rows)
    running = 0.0
    result = []
    for row in rows:
        hours = float(row.total_hours)
        running += hours
        result.append({"cause": row.cause, "total_hours": round(hours, 2), "cum_pct": round(100 * running / total, 2) if total else 0})
    return result


def equipment_reliability(db: Session, user) -> list[dict]:
    query = _scope(db.query(Equipment.name.label("equipment"), func.count(DelayEvent.id).label("failure_count"), func.avg(DelayEvent.eff_durn).label("mttr_hours"), func.sum(DelayEvent.eff_durn).label("total_downtime_hours")).join(DelayEvent), user)
    rows = query.group_by(Equipment.name).order_by(func.sum(DelayEvent.eff_durn).desc()).all()
    return [{"equipment": r.equipment, "failure_count": r.failure_count, "mttr_hours": round(float(r.mttr_hours), 2), "total_downtime_hours": round(float(r.total_downtime_hours), 2)} for r in rows]


def compare_shops(db: Session, user, shop_ids: list[int], metric: str, start_date: date | None, end_date: date | None) -> list[dict]:
    if metric not in {"eff_durn", "count", "mttr", "cause_breakdown"}:
        raise ValueError("Unsupported metric")
    permitted = shop_ids
    if not permitted:
        return []
    group_field = Agency.code.label("cause") if metric == "cause_breakdown" else DelayEvent.delay_date.label("date")
    query = db.query(Shop.name.label("shop"), group_field).join(DelayEvent).join(Agency).filter(DelayEvent.shop_id.in_(permitted))
    if start_date:
        query = query.filter(DelayEvent.delay_date >= start_date)
    if end_date:
        query = query.filter(DelayEvent.delay_date <= end_date)
    value = func.count(DelayEvent.id) if metric == "count" else func.avg(DelayEvent.eff_durn) if metric == "mttr" else func.sum(DelayEvent.eff_durn)
    rows = query.add_columns(value.label("value")).group_by(Shop.name, group_field).order_by(group_field).all()
    result = []
    for row in rows:
        record = {"shop": row.shop, "value": round(float(row.value), 2)}
        record["cause" if metric == "cause_breakdown" else "date"] = row.cause if metric == "cause_breakdown" else row.date.isoformat()
        result.append(record)
    return result


def assistant_context(db: Session, user) -> dict:
    return {"overview": overview(db, user), "pareto": pareto_by_cause(db, user)[:8], "equipment_reliability": equipment_reliability(db, user)[:8]}

def home_dashboard(db: Session, user) -> dict:
    query = _scope(db.query(DelayEvent), user)
    
    total_records = query.count()
    departments = query.join(Shop, DelayEvent.shop_id == Shop.id).with_entities(Shop.id).distinct().count()
    equipment_types = query.join(Equipment, DelayEvent.equipment_id == Equipment.id).with_entities(Equipment.id).distinct().count()
    agencies = query.join(Agency, DelayEvent.agency_id == Agency.id).with_entities(Agency.id).distinct().count()
    
    kpis = {
        "total_records": total_records,
        "departments": departments,
        "equipment_types": equipment_types,
        "agencies": agencies,
    }
    
    dept_counts = _scope(db.query(Shop.name.label("name"), func.count(DelayEvent.id).label("count")).join(DelayEvent, Shop.id == DelayEvent.shop_id), user)
    dept_counts = [{"name": r.name, "count": r.count} for r in dept_counts.group_by(Shop.name).order_by(func.count(DelayEvent.id).desc()).all()]
    
    eqpt_counts = _scope(db.query(Equipment.name.label("name"), func.count(DelayEvent.id).label("count")).join(DelayEvent, Equipment.id == DelayEvent.equipment_id), user)
    eqpt_counts = [{"name": r.name, "count": r.count} for r in eqpt_counts.group_by(Equipment.name).order_by(func.count(DelayEvent.id).desc()).limit(10).all()]
    
    agency_counts = _scope(db.query(Agency.code.label("name"), func.count(DelayEvent.id).label("count")).join(DelayEvent, Agency.id == DelayEvent.agency_id), user)
    agency_counts = [{"name": r.name, "count": r.count} for r in agency_counts.group_by(Agency.code).order_by(func.count(DelayEvent.id).desc()).all()]
    
    material_counts = _scope(db.query(DelayEvent.material.label("name"), func.count(DelayEvent.id).label("count")), user).filter(DelayEvent.material != None)
    material_counts = [{"name": r.name, "count": r.count} for r in material_counts.group_by(DelayEvent.material).order_by(func.count(DelayEvent.id).desc()).all()]
    
    reason_counts = _scope(db.query(DelayEvent.descr.label("name"), func.count(DelayEvent.id).label("count")), user).filter(DelayEvent.descr != None)
    reason_counts = [{"name": r.name, "count": r.count} for r in reason_counts.group_by(DelayEvent.descr).order_by(func.count(DelayEvent.id).desc()).limit(10).all()]

    return {
        "kpis": kpis,
        "department_delays": dept_counts,
        "top_equipment": eqpt_counts,
        "agency_distribution": agency_counts,
        "material_distribution": material_counts,
        "top_delay_reasons": reason_counts
    }
