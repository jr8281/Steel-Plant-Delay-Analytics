from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User
from app.schemas.schemas import AssistantQuestion, ChatRequest
from app.services.gemini_client import ask_assistant, chat_stream

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/query")
def query_assistant(payload: AssistantQuestion, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"answer": ask_assistant(payload.question, db, user), "grounding": "Live plant data"}

@router.post("/chat")
def chat_assistant(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Streaming chat endpoint for the AI Assistant."""
    return StreamingResponse(
        chat_stream(
            conversation_id=payload.conversation_id,
            message=payload.message,
            filters=payload.filters,
            db=db,
            user=user
        ),
        media_type="text/plain"
    )
