"""Seed PostgreSQL from an Excel file and create initial local dev accounts.

Usage: python seed.py ../data/sample_delay_logs.xlsx

Note: this script is for LOCAL DEVELOPMENT ONLY. Seeded accounts are created
with must_reset_password=True and should never be used as-is in a real deployment.
"""
import os
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import Shop, User
from app.services.ingestion import ingest_dataframe, load_and_clean

if len(sys.argv) < 2:
    raise SystemExit("Usage: python seed.py <path-to-delay-log.xlsx>")

DEFAULT_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
DEFAULT_OPERATOR_PASSWORD = os.getenv("SEED_OPERATOR_PASSWORD", "operator123")

db = SessionLocal()
try:
    count = ingest_dataframe(
        load_and_clean(Path(sys.argv[1])), db, replace_existing=True, filename=Path(sys.argv[1]).name
    )
    if not db.query(User).filter_by(username="admin").first():
        db.add(User(
            username="admin", hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            role="admin", must_reset_password=True,
        ))
    if not db.query(User).filter_by(username="operator").first():
        first_shop = db.query(Shop).order_by(Shop.id).first()
        db.add(User(
            username="operator", hashed_password=hash_password(DEFAULT_OPERATOR_PASSWORD),
            role="operator", shop_id=first_shop.id if first_shop else None, must_reset_password=True,
        ))
    db.commit()
    print(f"Imported {count} events. Dev accounts created with must_reset_password=True (if absent).")
finally:
    db.close()