import google.generativeai as genai

from app.core.config import settings
from app.services.analytics_engine import assistant_context

# In-memory conversation cache: conversation_id -> ChatSession
CONVERSATIONS = {}

def get_chat_session(conversation_id: str):
    if not settings.gemini_api_key:
        return None
    genai.configure(api_key=settings.gemini_api_key)
    if conversation_id not in CONVERSATIONS:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        CONVERSATIONS[conversation_id] = model.start_chat(history=[])
    return CONVERSATIONS[conversation_id]

def ask_assistant(question: str, db, user) -> str:
    # Legacy sync method for backward compatibility if needed
    context = assistant_context(db, user)
    if not settings.gemini_api_key:
        overview = context["overview"]
        return ("The grounded AI assistant needs a GEMINI_API_KEY to answer open-ended questions. "
                f"Current live snapshot: {overview['total_delay_hours']} delay hours across "
                f"{overview['total_delay_events']} events; highest-delay shop: {overview['worst_shop']}; "
                f"top delay cause: {overview['top_cause']}.")
    genai.configure(api_key=settings.gemini_api_key)
    prompt = f"""You are a steel plant operations assistant. Answer only from the live data below.
Do not invent values. If data is insufficient, say so plainly. Be concise and operational.
Live data: {context}
Question: {question}"""
    return genai.GenerativeModel("gemini-2.0-flash-lite").generate_content(prompt).text

def chat_stream(conversation_id: str, message: str, filters: dict | None, db, user):
    chat = get_chat_session(conversation_id)
    if not chat:
        # Fallback for no API key
        context = assistant_context(db, user)
        overview = context["overview"]
        yield (f"**I received your question:** '{message}'\n\n"
               "However, the grounded AI assistant needs a `GEMINI_API_KEY` configured in the backend environment to generate open-ended answers. "
               f"\n\n**Current Live Snapshot:**\n- **Total Delays**: {overview['total_delay_hours']} hours across {overview['total_delay_events']} events\n"
               f"- **Worst Shop**: {overview['worst_shop']}\n- **Top Cause**: {overview['top_cause']}")
        return

    context = assistant_context(db, user)
    
    # We inject the hidden context into the prompt, but we instruct the AI to treat it as context
    # while only answering the user's message.
    system_prompt = f"""[SYSTEM CONTEXT - DO NOT ACKNOWLEDGE THIS TEXT DIRECTLY]
You are a highly capable AI assistant for a Steel Plant Delay Analytics dashboard.
You must answer the user's questions based on the live operational data.
If the user's question relates to specific departments or causes, and they have filters active, focus on the filtered data.
Active Dashboard Filters: {filters}
Live Aggregate Data Context: {context}
[END SYSTEM CONTEXT]

User Question: {message}"""

    try:
        response = chat.send_message(system_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"Error communicating with AI: {str(e)}"
