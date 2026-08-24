"""
Groq AI Assistant with persistent chat history.

Maintains conversation history in database for multi-session access.
"""
import time
from typing import Any, Generator
from datetime import datetime

from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.analytics_engine import assistant_context
from app.models.models import ChatSession, ChatMessage, User

logger = get_logger(__name__)

_MODEL = "groq/compound"
_SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _get_client() -> Groq:
    """Get Groq API client."""
    return Groq(api_key=settings.groq_api_key)


def _get_or_create_session(session_id: str, user_id: int, db: Session) -> ChatSession:
    """Get existing session or create new one."""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    
    if not session:
        session = ChatSession(session_id=session_id, user_id=user_id)
        db.add(session)
        db.commit()
        db.refresh(session)
    else:
        # Update last accessed time
        session.last_accessed_at = datetime.utcnow()
        db.commit()
    
    return session


def _load_history(db: Session, session_id: str) -> list[dict[str, str]]:
    """Load message history from database."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()
    
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def _save_message(db: Session, session_id: str, role: str, content: str) -> None:
    """Save message to database."""
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    db.commit()
    logger.info(f"Saved chat message: session={session_id}, role={role}, length={len(content)}")


def ask_assistant(question: str, db: Session, user: User) -> str:
    """
    Ask assistant a one-off question (not part of session).
    
    Args:
        question: User's question
        db: Database session
        user: Authenticated user
    
    Returns:
        Response text
    """
    context = assistant_context(db, user)
    
    if not settings.groq_api_key:
        overview = context["overview"]
        return (
            "The grounded AI assistant needs a GROQ_API_KEY to answer open-ended questions. "
            f"Current live snapshot: {overview['total_delay_hours']} delay hours across "
            f"{overview['total_delay_events']} events; highest-delay shop: {overview['worst_shop']}; "
            f"top delay cause: {overview['top_cause']}."
        )
    
    prompt = f"""You are a steel plant operations assistant. Answer only from the live data below.
Do not invent values. If data is insufficient, say so plainly. Be concise and operational.

Live data: {context}

Question: {question}"""
    
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.exception(f"Groq request failed: {str(e)}")
        return "The AI assistant is temporarily unavailable. Please try again shortly."


def chat_stream(
    conversation_id: str,
    message: str,
    filters: dict | None,
    db: Session,
    user: User
) -> Generator[str, None, None]:
    """
    Stream chat response with persistent history.
    
    Args:
        conversation_id: Unique session identifier
        message: User's message
        filters: Optional dashboard filters
        db: Database session
        user: Authenticated user
    
    Yields:
        Response chunks
    """
    if not settings.groq_api_key:
        context = assistant_context(db, user)
        overview = context["overview"]
        yield (
            f"**I received your question:** '{message}'\n\n"
            "However, the grounded AI assistant needs a `GROQ_API_KEY` configured in the backend "
            "environment to generate open-ended answers."
            f"\n\n**Current Live Snapshot:**\n- **Total Delays**: {overview['total_delay_hours']} hours "
            f"across {overview['total_delay_events']} events\n"
            f"- **Worst Shop**: {overview['worst_shop']}\n- **Top Cause**: {overview['top_cause']}"
        )
        return

    # Get or create session
    chat_session = _get_or_create_session(conversation_id, user.id, db)
    
    # Load history from database
    history = _load_history(db, conversation_id)
    
    # Save user message
    _save_message(db, conversation_id, "user", message)
    
    context = assistant_context(db, user)

    system_message = {
        "role": "system",
        "content": (
            "You are a highly capable AI assistant for a Steel Plant Delay Analytics dashboard. "
            "Answer the user's questions based on the live operational data provided. "
            "If the user's question relates to specific departments or causes, and they have filters active, "
            "focus on the filtered data. Be concise, analytical, and operational.\n\n"
            f"Active Dashboard Filters: {filters}\n"
            f"Live Aggregate Data Context: {context}"
        ),
    }

    messages = [system_message] + history + [{"role": "user", "content": message}]

    try:
        client = _get_client()
        stream = client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            stream=True,
        )
        
        full_response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                yield delta

        # Save assistant response
        _save_message(db, conversation_id, "assistant", full_response)
        logger.info(f"Chat completed: user_id={user.id}, session={conversation_id}, response_len={len(full_response)}")

    except Exception as e:
        logger.exception(f"Groq streaming request failed for user_id={user.id}: {str(e)}")
        yield "The AI assistant hit an error processing that request. Please try again."


def get_session_history(session_id: str, user_id: int, db: Session) -> list[dict[str, str]]:
    """
    Retrieve full chat history for a session.
    
    Args:
        session_id: Session identifier
        user_id: User making request
        db: Database session
    
    Returns:
        List of messages with role and content
    """
    # Verify user owns this session
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        logger.warning(f"Unauthorized history access: user_id={user_id}, session={session_id}")
        return []
    
    return _load_history(db, session_id)


def delete_session(session_id: str, user_id: int, db: Session) -> bool:
    """
    Delete a chat session and all its messages.
    
    Args:
        session_id: Session identifier
        user_id: User making request
        db: Database session
    
    Returns:
        True if deleted, False if not found
    """
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        return False
    
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    
    logger.info(f"Deleted chat session: session_id={session_id}, user_id={user_id}")
    return True