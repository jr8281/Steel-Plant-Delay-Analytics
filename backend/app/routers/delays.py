from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging_config import get_logger  # <-- ADD THIS
from app.models.models import DelayEvent, User

logger = get_logger(__name__)  # <-- ADD THIS
router = APIRouter(prefix="/delays", tags=["Delays"])


@router.get("/", summary="List Delay Events")
def get_delays(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve delay events.
    
    For operators: Only their assigned shop's delays.
    For admins: All delays.
    """
    logger.info(f"user_id={user.id} role={user.role} fetching delays with skip={skip}, limit={limit}")
    
    try:
        query = db.query(DelayEvent)
        if user.role != "admin" and user.shop_id:
            query = query.filter(DelayEvent.shop_id == user.shop_id)
            logger.debug(f"Scoped query to shop_id={user.shop_id}")
        
        delays = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(delays)} delays for user_id={user.id}")
        return delays
    
    except Exception as e:
        logger.error(f"Failed to fetch delays for user_id={user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve delays")