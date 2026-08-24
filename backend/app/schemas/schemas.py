from typing import Any, List
from enum import Enum

# Add these after existing schemas...

class ErrorResponse(BaseModel):
    """Standard error response format."""
    detail: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of error")


class HealthResponse(BaseModel):
    """Service health check response."""
    status: str = Field(description="Status: 'ok' or 'degraded'")
    timestamp: str = Field(description="ISO timestamp")
    service: str = Field(description="Service name")


class PredictionResponse(BaseModel):
    """Delay duration prediction response."""
    predicted_bucket: str = Field(description="Predicted delay duration: 'short' (<2h), 'medium' (2-6h), or 'long' (>6h)")
    confidence: float = Field(ge=0, le=1, description="Prediction confidence (0.0 to 1.0)")
    probabilities: dict = Field(description="Probability distribution: {short, medium, long}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_bucket": "medium",
                "confidence": 0.78,
                "probabilities": {"short": 0.12, "medium": 0.78, "long": 0.10}
            }
        }


class AssistantMessageResponse(BaseModel):
    """AI Assistant response to a question."""
    question: str = Field(description="The user's original question")
    answer: str = Field(description="AI-generated answer based on live data")
    data_context: Optional[dict] = Field(default=None, description="Raw data used to ground the answer")
    confidence: Optional[float] = Field(default=None, description="Answer confidence level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Which equipment causes the most delays?",
                "answer": "Conveyor Belt is the top equipment causing 45 delays totaling 320 hours. It represents 28% of all delays in the database.",
                "confidence": 0.95
            }
        }


class UploadResponse(BaseModel):
    """File upload response."""
    status: str = Field(description="Status: 'success' or 'partial'")
    records_processed: int = Field(description="Number of records ingested")
    records_failed: int = Field(description="Number of records that failed validation")
    mode: str = Field(description="Upload mode used: 'append' or 'replace'")
    timestamp: str = Field(description="ISO timestamp of upload")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "records_processed": 152,
                "records_failed": 0,
                "mode": "append",
                "timestamp": "2026-08-24T10:30:00Z"
            }
        }