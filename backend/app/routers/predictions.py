from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.schemas import PredictionRequest, PredictionResponse
from app.core.database import get_db
from app.core.security import get_current_user
from app.ml.train_model import train
from app.ml.model_store import load_artifacts
import logging

router = APIRouter(prefix="/predictions", tags=["ML Predictions"])
logger = logging.getLogger(__name__)

@router.post(
    "/predict",
    response_model=PredictionResponse,  # <-- Use response model
    summary="Predict Delay Duration Risk",
    description="Predict whether a delay will be short (<2h), medium (2-6h), or long (>6h) based on historical patterns.",
    responses={
        200: {"description": "Prediction successful"},
        400: {"description": "Missing required fields"},
        401: {"description": "Unauthorized"},
        404: {"description": "Prediction model not found - train model first"},
        500: {"description": "Prediction inference failed"},
    },
)
def predict(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
) -> PredictionResponse:
    """
    Predict delay duration risk category.
    
    **Required Parameters:**
    - `shop_code`: Shop identifier
    - `agency_code`: Cause/agency code
    
    **Optional Parameters:**
    - `equipment_name`: Equipment identifier
    - `delay_date`: ISO date string (defaults to today)
    
    **Returns:**
    - `predicted_bucket`: Risk category (short/medium/long)
    - `confidence`: Model confidence (0-1)
    - `probabilities`: Per-bucket probability distribution
    
    **Example:**
```json
    {
      "shop_code": "01",
      "equipment_name": "Conveyor",
      "agency_code": "O",
      "delay_date": "2026-08-24"
    }
```
    """
    logger.info(f"Prediction request from user_id={user.id}: {request}")
    # ... implementation