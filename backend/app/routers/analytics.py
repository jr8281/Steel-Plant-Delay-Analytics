from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User
from app.services import analytics_engine as ae

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ae.overview(db, user)


@router.get("/home-dashboard")
def get_home_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ae.home_dashboard(db, user)


@router.get("/shop-breakdown")
def get_shop_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ae.shop_breakdown(db, user)


@router.get("/pareto")
def get_pareto(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ae.pareto_by_cause(db, user)


@router.get("/equipment/reliability")
def get_equipment_reliability(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ae.equipment_reliability(db, user)


@router.get("/compare")
def compare(shop_ids: list[int] = Query(...), metric: str = "eff_durn", start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return ae.compare_shops(db, user, shop_ids, metric, start_date, end_date)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc))
