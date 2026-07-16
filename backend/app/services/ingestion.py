"""Excel ingestion for the supplied steel-plant delay-log format."""
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Agency, DelayEvent, Equipment, Shop


def load_and_clean(filepath: str | Path) -> pd.DataFrame:
    filepath = str(filepath)
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath).drop(columns=["Rake"], errors="ignore")
    else:
        df = pd.read_excel(filepath).drop(columns=["Rake"], errors="ignore")
    required = {"Delay Date", "Shop Code", "Shop", "Durn", "Eff Durn", "agency"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Spreadsheet is missing required columns: {', '.join(sorted(missing))}")
    df["Delay Date"] = pd.to_datetime(df["Delay Date"], dayfirst=True, errors="coerce")
    if "Close Dt" in df:
        df["Close Dt"] = pd.to_datetime(df["Close Dt"], dayfirst=True, errors="coerce")
    for column in ["From", "Upto", "Durn", "Cum Delay", "Freq", "Eff Durn"]:
        if column in df:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["Shop Code", "Shop", "Eqpt", "Sub Eqpt", "agency", "Descr", "Contd", "Material", "Delay Code"]:
        if column in df:
            df[column] = df[column].astype("string").str.strip().replace({"": pd.NA})
    return df.dropna(subset=["Delay Date", "Shop Code", "Shop", "Durn", "Eff Durn", "agency"])


def _lookup_or_create(db: Session, model, field: str, value: str):
    item = db.query(model).filter(getattr(model, field) == value).first()
    if not item:
        item = model(**{field: value})
        db.add(item)
        db.flush()
    return item


def ingest_dataframe(df: pd.DataFrame, db: Session, replace_existing: bool = False) -> int:
    if replace_existing:
        db.query(DelayEvent).delete()
        db.flush()
    shops = {}
    for _, row in df[["Shop Code", "Shop"]].drop_duplicates().iterrows():
        shop = db.query(Shop).filter_by(shop_code=str(row["Shop Code"])).first()
        if not shop:
            shop = Shop(shop_code=str(row["Shop Code"]), name=str(row["Shop"]))
            db.add(shop)
            db.flush()
        shops[str(row["Shop Code"])] = shop
    equipment = {str(name): _lookup_or_create(db, Equipment, "name", str(name)) for name in df.get("Eqpt", pd.Series(dtype="object")).dropna().unique()}
    agencies = {str(code): _lookup_or_create(db, Agency, "code", str(code)) for code in df["agency"].dropna().unique()}
    for _, row in df.iterrows():
        value = lambda col: row[col] if col in row and pd.notna(row[col]) else None
        db.add(DelayEvent(
            delay_date=row["Delay Date"].date(), shop_id=shops[str(row["Shop Code"])].id,
            equipment_id=equipment.get(str(value("Eqpt"))).id if value("Eqpt") is not None else None,
            agency_id=agencies[str(row["agency"])].id, sub_eqpt=value("Sub Eqpt"),
            from_time=value("From"), upto_time=value("Upto"), durn=float(row["Durn"]),
            eff_durn=float(row["Eff Durn"]), cum_delay=float(value("Cum Delay") or 0),
            freq=int(value("Freq") or 1), descr=value("Descr"), material=value("Material"),
            delay_code=value("Delay Code"), contd=value("Contd"),
            close_dt=value("Close Dt").date() if value("Close Dt") is not None else None,
        ))
    db.commit()
    return len(df)
