"""Seed PostgreSQL from an Excel file and create initial local accounts.

Usage: python seed.py ../data/sample_delay_logs.xlsx
"""
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import Shop, User
from app.services.ingestion import ingest_dataframe, load_and_clean

if len(sys.argv) < 2:
    raise SystemExit("Usage: python seed.py <path-to-delay-log.xlsx>")

db = SessionLocal()
try:
    count = ingest_dataframe(load_and_clean(Path(sys.argv[1])), db, replace_existing=True)
    if not db.query(User).filter_by(username="admin").first():
        db.add(User(username="admin", hashed_password=hash_password("admin123"), role="admin"))
    if not db.query(User).filter_by(username="operator").first():
        first_shop = db.query(Shop).order_by(Shop.id).first()
        db.add(User(username="operator", hashed_password=hash_password("operator123"), role="operator", shop_id=first_shop.id if first_shop else None))
    db.commit()
    print(f"Imported {count} events. Created accounts only when absent.")
finally:
    db.close()
