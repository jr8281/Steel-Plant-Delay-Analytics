import streamlit as st
import uuid
import os
import requests

def stream_api_request(method, path, **kwargs):
    API = os.getenv("API_BASE_URL", "http://localhost:8000")
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with requests.request(method, f"{API}{path}", headers=headers, stream=True, timeout=120, **kwargs) as r:
            if not r.ok:
                yield "Error: Unable to contact the AI Assistant."
                return
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except Exception as e:
        yield f"Error: Unable to connect to the backend API. {e}"

def render():
    st.markdown('<div class="page-title">Steel Plant AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-secondary); margin-top: -15px; margin-bottom: 20px;">Ask questions about delay analytics, production performance and operational insights.</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* Fix chat input positioning and overlay */
    .block-container {
        padding-bottom: 150px !important;
    }
    
    .stChatFloatingInputContainer {
        background-color: #0F172A !important;
        padding-bottom: 20px;
        z-index: 9999;
    }
    
    /* Style the chat input box */
    [data-testid="stChatInput"] {
        background-color: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stChatInput"] textarea {
        color: #F8FAFC !important;
    }
    
    /* Base message container styling */
    [data-testid="stChatMessage"] {
        padding: 20px !important;
        border-radius: 16px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        border: none !important;
    }
    
    /* User Message styling using :has() selector */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: linear-gradient(135deg, #1E40AF, #3B82F6) !important;
        color: #F8FAFC !important;
    }
    
    /* Assistant Message styling */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background: #1E293B !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #E2E8F0 !important;
    }
    
    /* Make text inside messages white-ish for better contrast */
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
        color: #F8FAFC !important;
        font-family: 'Inter', 'Manrope', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 💬 AI Options")
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.rerun()
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
            
        st.markdown("### 🔍 Recent Questions")
        queries = [
            "Which department had the highest delay today?",
            "Why is COCCP having more delays?",
            "Show the top five delay causes."
        ]
        for q in queries:
            if st.button(q, use_container_width=True):
                st.session_state.pending_query = q
                st.rerun()

    # Initialize chat history and conversation id
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())

    # Render Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    prompt = st.chat_input("Ask anything about the steel plant...")
    
    # Handle auto-query from sidebar buttons
    if "pending_query" in st.session_state:
        prompt = st.session_state.pending_query
        del st.session_state.pending_query

    # Process new user input
    if prompt:
        # Append User Message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Append Assistant Response Stream
        with st.chat_message("assistant"):
            filters = st.session_state.get("dashboard_filters", {})
            payload = {
                "conversation_id": st.session_state.conversation_id,
                "message": prompt,
                "filters": filters
            }
            
            with st.spinner("Steel Plant AI is thinking..."):
                response_stream = stream_api_request("POST", "/assistant/chat", json=payload)
                full_response = st.write_stream(response_stream)
                
            # Save assistant response to history
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
