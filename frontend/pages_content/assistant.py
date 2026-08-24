"""AI Assistant chat interface with persistent history."""

import streamlit as st
import uuid
from pages_content.utils import api_request

def render():
    """Render AI Assistant chat interface."""
    st.markdown('<h1 style="font-size: 28px; margin-bottom: 20px;">🤖 AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown("Ask questions about your plant data in natural language. Your chat history is saved automatically.")
    st.markdown("---")
    
    # Initialize session state
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())
        st.session_state.chat_messages = []
    
    # Sidebar for session management
    with st.sidebar:
        st.markdown("### 💬 Chat Sessions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Chat", use_container_width=True):
                st.session_state.chat_session_id = str(uuid.uuid4())
                st.session_state.chat_messages = []
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear History", use_container_width=True):
                # Delete session from database
                api_request("DELETE", f"/assistant/history/{st.session_state.chat_session_id}")
                st.session_state.chat_messages = []
                st.rerun()
        
        st.markdown(f"**Session ID:** `{st.session_state.chat_session_id[:8]}...`")
        
        st.markdown("### 💡 Example Questions")
        examples = [
            "Which equipment causes the most delays?",
            "What's the average delay duration by shop?",
            "Which agency has the highest MTTR?",
            "Show me delays from the past week",
        ]
        for example in examples:
            if st.button(example, use_container_width=True, key=f"example_{example[:20]}"):
                st.session_state.user_message = example
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])
    
    # Chat input
    st.markdown("---")
    
    # Get optional filters from query params
    filters = {}
    
    if prompt := st.chat_input("Ask me about your plant data..."):
        # Add user message to history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("Thinking..."):
                # Stream response from API
                response = api_request(
                    "POST",
                    "/assistant/chat",
                    {
                        "conversation_id": st.session_state.chat_session_id,
                        "message": prompt,
                        "filters": filters,
                    },
                    stream=True
                )
                
                if response:
                    # Handle streaming response
                    if hasattr(response, 'iter_content'):
                        for chunk in response.iter_content(decode_unicode=True):
                            if chunk:
                                full_response += chunk
                                message_placeholder.markdown(full_response + "▌")
                    else:
                        full_response = response if isinstance(response, str) else str(response)
                        message_placeholder.markdown(full_response)
                
                message_placeholder.markdown(full_response)
        
        # Add assistant message to history
        st.session_state.chat_messages.append({"role": "assistant", "content": full_response})