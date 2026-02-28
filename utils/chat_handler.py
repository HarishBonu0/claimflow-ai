"""
Chat Handler - Manages conversation logic and responses
"""

import time
from datetime import datetime


class ChatHandler:
    """Handles chat logic, responses, and conversation flow"""
    
    @staticmethod
    def generate_response(user_message: str, knowledge_base) -> str:
        """
        Generate intelligent response based on user message
        
        Args:
            user_message: User's input message
            knowledge_base: Reference to knowledge base
            
        Returns:
            AI response string
        """
        user_message_lower = user_message.lower()
        
        # Check for guardrails triggers
        if any(phrase in user_message_lower for phrase in [
            "should i buy", "which insurance", "will my claim be approved",
            "guarantee", "recommend buying", "best insurance"
        ]):
            return knowledge_base.get_guardrail_response()
        
        # Savings/Financial Planning
        if any(word in user_message_lower for word in ["savings", "save", "compound", "growth", "invest"]):
            return knowledge_base.get_savings_info()
        
        # Claims Process
        if any(word in user_message_lower for word in ["claim", "process", "stages", "steps"]):
            return knowledge_base.get_claims_process()
        
        # Documentation
        if any(word in user_message_lower for word in ["document", "documents", "required", "need"]):
            return knowledge_base.get_documentation_info()
        
        # Delays
        if any(word in user_message_lower for word in ["delay", "delayed", "slow", "waiting", "taking long"]):
            return knowledge_base.get_delay_reasons()
        
        # Tracking
        if any(word in user_message_lower for word in ["track", "status", "check", "follow up"]):
            return knowledge_base.get_tracking_info()
        
        # Default response
        return knowledge_base.get_default_response()
    
    @staticmethod
    def simulate_streaming(text: str, placeholder):
        """
        Simulate ChatGPT-style streaming effect
        
        Args:
            text: Full text to display
            placeholder: Streamlit placeholder for text
        """
        displayed_text = ""
        for char in text:
            displayed_text += char
            placeholder.markdown(displayed_text + "▌")
            time.sleep(0.01)  # Adjust speed as needed
        placeholder.markdown(text)
    
    @staticmethod
    def create_chat_title(message: str, max_length: int = 50) -> str:
        """Create a title for chat history from first message"""
        if len(message) <= max_length:
            return message
        return message[:max_length] + "..."
    
    @staticmethod
    def save_chat_session(messages: list) -> dict:
        """Save current chat session"""
        if not messages:
            return None
        
        # Get first user message as title
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        title = ChatHandler.create_chat_title(user_messages[0]["content"]) if user_messages else "New Chat"
        
        return {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "title": title,
            "messages": messages.copy(),
            "timestamp": datetime.now()
        }
