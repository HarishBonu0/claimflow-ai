"""
ClaimFlow AI - Insurance Claims & Financial Literacy Assistant
Minimal ChatGPT-Style Interface
"""

import streamlit as st
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import integration layer and safety modules
from llm.integration_example import answer_query
from llm.safety_filter import check_safety
from llm.intent_classifier import IntentClassifier

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="ClaimFlow AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS - MINIMAL CHATGPT STYLE
# ============================================
st.markdown("""
<style>
    /* Import Clean Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark Background */
    .stApp {
        background: #0f172a;
    }
    
    .main {
        background: #0f172a;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove Default Padding */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Top Bar */
    .top-bar {
        background: #1e293b;
        padding: 0.75rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #334155;
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    .app-title {
        color: #f1f5f9;
        font-size: 0.95rem;
        font-weight: 600;
    }
    
    .trust-badge {
        background: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #1e293b;
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: #1e293b;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent;
        color: #e2e8f0;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        font-size: 0.875rem;
        width: 100%;
        transition: all 0.2s;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #334155;
        border-color: #64748b;
    }
    
    /* New Chat Button */
    .stButton > button[key="new_chat"] {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton > button[key="new_chat"]:hover {
        background: #2563eb !important;
    }
    
    /* Chat Container - Narrow & Centered */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem 6rem 1rem;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: transparent;
        padding: 1rem 0;
    }
    
    /* Assistant Messages */
    [data-testid="stChatMessageContent"] {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        color: #e2e8f0;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* User Messages */
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
        background: #3b82f6;
        color: white;
        border: none;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 21rem;
        right: 0;
        background: #0f172a;
        border-top: 1px solid #334155;
        padding: 1rem;
        z-index: 999;
    }
    
    .stChatInputContainer > div {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .stChatInput > div {
        background: #1e293b;
        border: 1px solid #475569;
        border-radius: 12px;
    }
    
    .stChatInput input {
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    
    .stChatInput input::placeholder {
        color: #64748b;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #94a3b8;
    }
    
    .empty-state h2 {
        color: #f1f5f9;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .empty-state p {
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }
    
    /* Suggestion Buttons */
    .suggestion-btn {
        background: #1e293b;
        border: 1px solid #475569;
        color: #e2e8f0;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.5rem;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
        display: inline-block;
    }
    
    .suggestion-btn:hover {
        background: #334155;
        border-color: #3b82f6;
    }
    
    /* Warning Card */
    .warning-card {
        background: rgba(251, 191, 36, 0.1);
        border: 1px solid rgba(251, 191, 36, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #fbbf24;
        font-size: 0.85rem;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #94a3b8;
        font-size: 0.85rem;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_response(user_input):
    """Generate AI response with safety checks and intent classification"""
    try:
        logger.info(f"Processing query: {user_input[:50]}...")
        
        # Step 1: Intent classification
        intent, confidence = IntentClassifier.classify(user_input)
        logger.info(f"Intent: {intent} (confidence: {confidence:.2f})")
        
        # Step 2: Safety check (pre-LLM guardrails)
        is_safe, rejection_message = check_safety(user_input)
        if not is_safe:
            logger.warning(f"Query blocked by safety filter: {intent}")
            return rejection_message
        
        # Step 3: Use proper integration layer (RAG + LLM)
        response = answer_query(user_input, context_k=3, verbose=False)
        logger.info(f"Response generated: {len(response)} characters")
        
        return response
    
    except Exception as e:
        # Fallback error message
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return f"""
⚠️ **Service Temporarily Unavailable**

I encountered an error processing your question. This could be due to:
- API rate limits
- Network connectivity issues
- Service maintenance

**Error details**: {str(e)[:100]}

Please try again in a moment, or rephrase your question.
"""

# ============================================
# TOP BAR
# ============================================
st.markdown("""
<div class='top-bar'>
    <div class='app-title'>ClaimFlow AI</div>
    <div class='trust-badge'>Educational Only</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("<h3 style='color: #f1f5f9; font-size: 1rem; margin-bottom: 1rem;'>💬 Chat History</h3>", unsafe_allow_html=True)
    
    # New Chat Button
    if st.button("➕ New Chat", key="new_chat", use_container_width=True):
        if st.session_state.messages:
            # Save current chat
            user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
            if user_messages:
                chat_title = user_messages[0]["content"][:40] + "..." if len(user_messages[0]["content"]) > 40 else user_messages[0]["content"]
            else:
                chat_title = "New Conversation"
            
            chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.session_state.chat_history.insert(0, {
                "id": chat_id,
                "title": chat_title,
                "messages": st.session_state.messages.copy()
            })
        
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Chat History List
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(chat["title"], key=f"chat_{chat['id']}", use_container_width=True):
                    st.session_state.messages = chat["messages"].copy()
                    st.session_state.current_chat_id = chat["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{chat['id']}"):
                    st.session_state.chat_history = [c for c in st.session_state.chat_history if c["id"] != chat["id"]]
                    if st.session_state.current_chat_id == chat["id"]:
                        st.session_state.messages = []
                        st.session_state.current_chat_id = None
                    st.rerun()
    else:
        st.markdown("<p style='color: #64748b; text-align: center; padding: 2rem 1rem; font-size: 0.85rem;'>No previous chats</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Clear All Button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear All Chats", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.messages = []
            st.session_state.current_chat_id = None
            st.rerun()
    
    st.markdown("<div style='margin-top: auto; padding-top: 2rem;'>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; font-size: 0.75rem;'>Version 1.0.0</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# MAIN CHAT AREA
# ============================================
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# Empty State
if not st.session_state.messages:
    st.markdown("""
    <div class='empty-state'>
        <h2>ClaimFlow AI</h2>
        <p>Ask about insurance claims or savings growth.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Explain claim stages", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Explain claim stages"})
            st.rerun()
    with col2:
        if st.button("⏱️ Why is my claim delayed?", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Why is my claim delayed?"})
            st.rerun()
    with col3:
        if st.button("📄 What documents are required?", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What documents are required?"})
            st.rerun()
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("💰 Show savings growth example", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Show savings growth example"})
            st.rerun()

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🛡️"):
        st.markdown(message["content"])

st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# CHAT INPUT
# ============================================
if prompt := st.chat_input("Ask about insurance claims or savings growth..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate response
    response = generate_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Rerun to display
    st.rerun()
