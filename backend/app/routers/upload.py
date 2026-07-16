import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin, User
from app.services.ingestion import ingest_dataframe, load_and_clean

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin)
):
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV or Excel files are allowed.")
    
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        df = load_and_clean(tmp_path)
        count = ingest_dataframe(df, db, replace_existing=True)
        return {"message": "Successfully uploaded and ingested data.", "records_ingested": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
