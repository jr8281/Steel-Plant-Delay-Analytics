from typing import Optional
from pydantic import BaseModel, Field

class FilterConfig(BaseModel):
    """Validated filter configuration for dashboard queries."""
    shop_code: Optional[str] = Field(default=None, max_length=10)
    equipment_name: Optional[str] = Field(default=None, max_length=100)
    agency_code: Optional[str] = Field(default=None, max_length=10)
    start_date: Optional[str] = Field(default=None)  # ISO format
    end_date: Optional[str] = Field(default=None)    # ISO format

    class Config:
        json_schema_extra = {
            "example": {
                "shop_code": "01",
                "equipment_name": "Conveyor",
                "agency_code": "O"
            }
        }

# Update ChatRequest
class ChatRequest(BaseModel):
    """Chat message request with validated filters."""
    conversation_id: str
    message: str = Field(min_length=1, max_length=2000)
    filters: Optional[FilterConfig] = None  # <-- Now typed and validated