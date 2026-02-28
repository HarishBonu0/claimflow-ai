"""
UI Components - Reusable UI elements
"""

import streamlit as st


class UIComponents:
    """Reusable UI components for ClaimFlow AI"""
    
    @staticmethod
    def render_hero_section():
        """Render the hero section shown when no messages exist"""
        st.markdown("""
        <div class='hero-section'>
            <div class='hero-icon'>🛡️</div>
            <h1 class='hero-title'>ClaimFlow AI</h1>
            <p class='hero-subtitle'>Ask about insurance claims or savings growth.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick suggestion buttons
        st.markdown("<div class='suggestions-container'>", unsafe_allow_html=True)
        st.markdown("<p class='suggestions-title'>Try asking:</p>", unsafe_allow_html=True)
        
        cols = st.columns(2)
        suggestions = [
            "Explain claim stages",
            "Why is my claim delayed?",
            "What documents are required?",
            "Show savings growth example"
        ]
        
        for idx, suggestion in enumerate(suggestions):
            col = cols[idx % 2]
            with col:
                if st.button(suggestion, key=f"suggestion_{idx}", use_container_width=True):
                    return suggestion
        
        st.markdown("</div>", unsafe_allow_html=True)
        return None
    
    @staticmethod
    def render_guardrail_warning():
        """Render a professional guardrail warning card"""
        st.markdown("""
        <div class='guardrail-card'>
            <div class='guardrail-icon'>⚠️</div>
            <div class='guardrail-content'>
                <h4>Educational Guidance Only</h4>
                <p>I can explain insurance processes and financial concepts, but I cannot make claim decisions or provide specific financial advice. Please consult with your insurance provider or financial advisor for personalized recommendations.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_top_bar():
        """Render the top navigation bar"""
        st.markdown("""
        <div class='top-bar'>
            <div class='top-bar-content'>
                <div class='app-branding'>
                    <span class='app-icon'>🛡️</span>
                    <span class='app-name'>ClaimFlow AI</span>
                    <span class='app-tagline'>Understand your insurance. Plan your savings.</span>
                </div>
                <div class='trust-badge'>
                    <span class='badge-icon'>🎓</span>
                    <span>Educational Guidance Only</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_sidebar(chat_history, current_chat_id, clear_callback, new_chat_callback, load_chat_callback, delete_chat_callback):
        """
        Render ChatGPT-style sidebar
        
        Args:
            chat_history: List of previous chats
            current_chat_id: ID of current active chat
            clear_callback: Function to call when clearing chat
            new_chat_callback: Function to call for new chat
            load_chat_callback: Function to call when loading a chat
            delete_chat_callback: Function to call when deleting a chat
        """
        with st.sidebar:
            # New Chat Button
            if st.button("➕ New Chat", key="new_chat_sidebar", use_container_width=True, type="primary"):
                new_chat_callback()
            
            st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
            
            # Chat History Header
            st.markdown("<div class='sidebar-section-title'>Recent Conversations</div>", unsafe_allow_html=True)
            
            # Display chat history
            if chat_history:
                for chat in chat_history:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        active = current_chat_id == chat["id"]
                        button_type = "primary" if active else "secondary"
                        if st.button(
                            chat["title"],
                            key=f"load_chat_{chat['id']}",
                            use_container_width=True,
                            type=button_type
                        ):
                            load_chat_callback(chat)
                    with col2:
                        if st.button("🗑️", key=f"delete_chat_{chat['id']}"):
                            delete_chat_callback(chat["id"])
            else:
                st.markdown("""
                <div class='empty-history'>
                    <p>No conversations yet.</p>
                    <p>Start a new chat!</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
            
            # Clear All Button
            if st.button("🗑️ Clear All Chats", key="clear_all", use_container_width=True):
                clear_callback()
            
            # Footer
            st.markdown("""
            <div class='sidebar-footer'>
                <div class='version-info'>
                    <strong>Version</strong> 1.0.0
                </div>
                <div class='powered-by'>
                    Powered by ClaimFlow AI
                </div>
            </div>
            """, unsafe_allow_html=True)
