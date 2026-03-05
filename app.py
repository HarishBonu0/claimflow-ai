"""
ClaimFlow AI - Insurance Claims & Financial Literacy Assistant
Minimal ChatGPT-Style Interface
"""

import streamlit as st
import time
from datetime import datetime

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
    """Generate AI response based on user input"""
    time.sleep(0.8)  # Simulate processing
    
    # Check for guardrails
    guardrail_triggers = ["will my claim be approved", "which insurance should i buy", "guarantee", "recommend insurance"]
    if any(trigger in user_input.lower() for trigger in guardrail_triggers):
        return """
⚠️ **Important Notice**

I can explain insurance processes and concepts, but I cannot:
- Predict claim approval outcomes
- Recommend specific insurance products
- Make financial decisions for you

I'm here to help you **understand** insurance and savings concepts so you can make informed decisions. 

Would you like me to explain how claim evaluation works instead?
"""
    
    # Insurance claims questions
    if any(word in user_input.lower() for word in ["claim", "process", "stages", "steps"]):
        return """
**Insurance Claims Process**

Here's how insurance claims typically work:

1. **Claim Filing** - Submit your claim with necessary documents within the specified timeframe
2. **Acknowledgment** - Insurer acknowledges receipt (usually within 24-48 hours)
3. **Document Verification** - Claims team reviews submitted documents
4. **Investigation** - If needed, surveyor assesses the claim
5. **Decision** - Claim is approved, rejected, or more info is requested
6. **Settlement** - Approved amount is disbursed

**Timeline**: Most claims are processed within 15-30 days.

**Tip**: Keep all original documents and maintain clear communication with your insurer.
"""
    
    # Delay questions
    if "delay" in user_input.lower():
        return """
**Common Reasons for Claim Delays**

Your claim might be delayed due to:

- **Missing Documents** - Incomplete paperwork is the #1 cause
- **Verification Pending** - Additional information needed
- **Complex Cases** - High-value or unusual claims take longer
- **Peak Periods** - During disasters, processing slows down
- **Discrepancies** - Conflicting information in documents

**What You Can Do:**
- Follow up regularly
- Provide complete documentation upfront
- Respond quickly to insurer requests
- Keep records of all communication
"""
    
    # Documents
    if "document" in user_input.lower():
        return """
**Required Documents for Claims**

**Health Insurance:**
- Hospital bills and receipts
- Discharge summary
- Diagnostic reports
- Prescription and pharmacy bills
- Doctor's certificate

**Motor Insurance:**
- FIR copy (for theft/accident)
- Driving license
- RC book copy
- Repair estimates
- Photos of damage

**Life Insurance:**
- Death certificate
- Claim form
- Policy document
- ID proof of beneficiary

**Pro Tip**: Keep digital copies of all documents for faster processing.
"""
    
    # Savings questions
    if any(word in user_input.lower() for word in ["savings", "growth", "compound", "investment", "sip"]):
        return """
**Savings Growth Through Compounding**

Compound interest is earning interest on your interest. Here's how it works:

**Example:**
- Initial Amount: ₹10,000
- Annual Return: 8%
- After 10 years: ₹21,589
- After 20 years: ₹46,610
- After 30 years: ₹1,00,627

**Key Principles:**
1. **Start Early** - Time is your biggest advantage
2. **Stay Consistent** - Regular investments (SIP) work best
3. **Be Patient** - Compounding accelerates over time
4. **Diversify** - Spread risk across different options

**Popular Options:**
- Fixed Deposits (Safe, 5-7% returns)
- Mutual Funds (Moderate risk, 10-12% potential)
- PPF (Tax-free, 7-8% returns)
- Stocks (High risk, variable returns)

💡 **Remember**: Past performance doesn't guarantee future results. Always assess your risk tolerance.
"""
    
    # Default response
    return """
I'm ClaimFlow AI, your insurance and savings guide. I can help you with:

- **Insurance Claims** - Understanding the process, timelines, and requirements
- **Savings Growth** - Learning about compound interest and investment principles
- **Documents** - Knowing what paperwork you need
- **Common Issues** - Delays, rejections, and how to handle them

What would you like to know more about?
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
