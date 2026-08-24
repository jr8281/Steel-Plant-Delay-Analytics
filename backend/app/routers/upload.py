# Example improvement
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

@router.post("/upload/csv")
async def upload_csv(
    file: UploadFile = File(..., description="CSV or Excel file with delay log data"),
    mode: str = Query("append", regex="^(append|replace)$", description="Append new data or replace all"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:  # <-- Add return type
    """Upload and ingest delay log data."""
    # ... implementation