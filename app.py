"""
ClaimFlow AI - Insurance Claims & Financial Literacy Assistant
Minimal ChatGPT-Style Interface with Voice Input/Output
"""

import streamlit as st
import time
import logging
import os
import tempfile
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

# Import voice modules
try:
    from voice.stt import speech_to_text
    from voice.tts import text_to_speech, play_audio
    VOICE_ENABLED = True
except ImportError:
    logger.warning("Voice modules not available. Voice features disabled.")
    VOICE_ENABLED = False

# Language mapping for TTS
LANGUAGE_CODES = {
    'English': 'en',
    'Hindi': 'hi',
    'Telugu': 'te',
    'Tamil': 'ta',
    'Kannada': 'kn',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Portuguese': 'pt',
    'Japanese': 'ja',
    'Chinese (Simplified)': 'zh-cn',
    'Chinese (Traditional)': 'zh-tw',
}

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
    
    /* Warm Cream Background */
    .stApp {
        background: #FAF9F7;
    }
    
    .main {
        background: #FAF9F7;
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
    
    /* Top Bar - Deep Emerald */
    .top-bar {
        background: #047857;
        padding: 0.75rem 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #047857;
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    .app-title {
        color: #FFFFFF;
        font-size: 0.95rem;
        font-weight: 600;
    }
    
    .trust-badge {
        background: rgba(217, 119, 6, 0.1);
        color: #D97706;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        border: 1px solid rgba(217, 119, 6, 0.3);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: #FFFFFF;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent;
        color: #047857;
        border: 1px solid #047857;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        font-size: 0.875rem;
        width: 100%;
        transition: all 0.2s;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #D1FAE5;
        border-color: #047857;
    }
    
    /* New Chat Button */
    .stButton > button[key="new_chat"] {
        background: #047857 !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton > button[key="new_chat"]:hover {
        background: #065F46 !important;
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
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        color: #1F2937;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* User Messages */
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
        background: #D1FAE5;
        color: #1F2937;
        border: none;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 21rem;
        right: 0;
        background: #FAF9F7;
        border-top: 1px solid #E5E7EB;
        padding: 1rem;
        z-index: 999;
    }
    
    .stChatInputContainer > div {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .stChatInput > div {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
    }
    
    .stChatInput input {
        color: #1F2937;
        font-size: 0.9rem;
    }
    
    .stChatInput input::placeholder {
        color: #6B7280;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #6B7280;
    }
    
    .empty-state h2 {
        color: #1F2937;
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
        background: #D1FAE5;
        border: 1px solid #047857;
        color: #1F2937;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.5rem;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
        display: inline-block;
    }
    
    .suggestion-btn:hover {
        background: #047857;
        color: #FFFFFF;
        border-color: #047857;
    }
    
    /* Warning Card */
    .warning-card {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #F59E0B;
        font-size: 0.85rem;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #1F2937;
        font-size: 0.85rem;
    }
    
    /* Voice input styling */
    [data-testid="stSidebar"] .stAudio,
    [data-testid="stSidebar"] .stSelectbox {
        margin-bottom: 0.5rem;
    }
    
    /* Chat input container */
    .stChatInput button[data-testid="baseButton-secondary"] {
        color: #1F2937;
        border: 1px solid #E5E7EB;
    }
    
    /* Voice & Generate buttons */
    [data-testid="baseButton-secondary"] button {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
    }
    
    [data-testid="baseButton-secondary"] button:hover {
        background: #D1FAE5;
    }
    
    /* Professional Mic Button - Inside Input ChatGPT Style */
    [data-testid="stChatInputContainer"] {
        position: relative;
    }
    
    /* Unified Input with Mic Button */
    .input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .input-wrapper > div:first-child {
        flex: 1;
    }
    
    button[key="voice_record_btn"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        border-radius: 50% !important;
        background: transparent !important;
        border: none !important;
        color: #047857 !important;
        font-size: 1.2rem !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        flex-shrink: 0 !important;
        position: relative !important;
    }
    
    button[key="voice_record_btn"]:hover {
        color: #065F46 !important;
        background: rgba(4, 120, 87, 0.05) !important;
    }
    
    button[key="voice_record_btn"]:active {
        background: rgba(4, 120, 87, 0.15) !important;
        color: #065F46 !important;
        transform: scale(0.95) !important;
    }
    
    /* Voice generation & other buttons */
    button[key="gen_voice_btn"],
    button[key="process_voice"],
    button[key="gen_voice_go"] {
        min-height: 44px;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Audio input styling */
    [data-testid="stAudioInput"] {
        margin: 1rem 0;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] button {
        background: #FAF9F7;
        border: 1px solid #E5E7EB;
        color: #1F2937;
        font-size: 0.85rem;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: #047857;
        border: 1px solid #047857;
        color: #FFFFFF;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #FAF9F7;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #D1D5DB;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #047857;
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

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = VOICE_ENABLED

if "selected_language" not in st.session_state:
    st.session_state.selected_language = 'English'

if "last_voice_response_audio" not in st.session_state:
    st.session_state.last_voice_response_audio = None

if "show_voice_recorder" not in st.session_state:
    st.session_state.show_voice_recorder = False

if "show_voice_gen" not in st.session_state:
    st.session_state.show_voice_gen = False

# ============================================
# VOICE PROCESSING FUNCTIONS
# ============================================

def process_voice_input(audio_file, language_code):
    """
    Process voice input: convert to text and generate response.
    
    Args:
        audio_file: Path to audio file
        language_code: Language code for TTS output
    
    Returns:
        Dictionary with user_text, response_text, and audio_file
    """
    try:
        logger.info("Starting voice input processing...")
        
        # Step 1: Speech to Text (Whisper auto-detects language)
        logger.info("Converting speech to text...")
        user_text = speech_to_text(audio_file)
        
        if user_text.startswith("Error:"):
            logger.error(f"STT failed: {user_text}")
            return {
                'user_text': '',
                'response_text': 'Sorry, I could not understand your speech. Please try again.',
                'audio_file': None,
                'success': False
            }
        
        logger.info(f"Transcribed text: {user_text[:50]}...")
        
        # Step 2: Generate response (using text pipeline)
        response_text = generate_response(user_text)
        logger.info(f"Generated response: {len(response_text)} characters")
        
        # Step 3: Text to Speech (using selected language)
        logger.info(f"Converting response to speech ({language_code})...")
        audio_file_output = f"temp_response_{int(time.time())}.mp3"
        audio_path = text_to_speech(response_text, audio_file_output, language=language_code)
        
        if not audio_path:
            logger.warning("TTS conversion failed")
            return {
                'user_text': user_text,
                'response_text': response_text,
                'audio_file': None,
                'success': True  # Text response is still valid
            }
        
        logger.info(f"Audio generated: {audio_path}")
        
        return {
            'user_text': user_text,
            'response_text': response_text,
            'audio_file': audio_path,
            'success': True
        }
    
    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}", exc_info=True)
        return {
            'user_text': '',
            'response_text': f'Error processing voice: {str(e)[:100]}',
            'audio_file': None,
            'success': False
        }

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
    # ============================================
    # LANGUAGE SELECTION (for voice output)
    # ============================================
    if VOICE_ENABLED:
        st.markdown("<h3 style='color: #f1f5f9; font-size: 1rem; margin-bottom: 1rem;'>🌍 Language Settings</h3>", unsafe_allow_html=True)
        
        selected_lang = st.selectbox(
            "Voice Response Language",
            list(LANGUAGE_CODES.keys()),
            index=list(LANGUAGE_CODES.keys()).index(st.session_state.selected_language),
            key="language_select"
        )
        st.session_state.selected_language = selected_lang
        st.caption(f"Responses will be in {selected_lang}")
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
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
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🛡️"):
        st.markdown(message["content"])
        
        # Add audio playback button for assistant messages with voice responses
        if message["role"] == "assistant" and st.session_state.last_voice_response_audio:
            if st.session_state.messages[i] is message:  # Last assistant message
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🔊 Play", key=f"play_audio_{i}"):
                        try:
                            with open(st.session_state.last_voice_response_audio, 'rb') as audio_file:
                                st.audio(audio_file.read(), format='audio/mp3')
                        except Exception as e:
                            st.error(f"Could not play audio: {str(e)}")
                
                with col2:
                    st.markdown("<p style='color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;'>Listen to response</p>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# AUDIO PLAYBACK SECTION (for latest voice response)
# ============================================
if st.session_state.last_voice_response_audio and os.path.exists(st.session_state.last_voice_response_audio):
    st.divider()
    st.markdown("<h4 style='color: #f1f5f9; margin-bottom: 1rem;'>🔊 Voice Response</h4>", unsafe_allow_html=True)
    
    try:
        with open(st.session_state.last_voice_response_audio, 'rb') as audio_file:
            audio_data = audio_file.read()
            st.audio(audio_data, format='audio/mp3', use_column_width=True)
            st.markdown(f"<p style='color: #94a3b8; font-size: 0.75rem;'>Language: {st.session_state.selected_language}</p>", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error playing audio: {str(e)}")
        st.warning(f"Could not load voice response: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# CHAT INPUT with VOICE
# ============================================

# Create a container for input controls
input_container = st.container()

with input_container:
    col1, col2 = st.columns([1, 0.08], gap="small")
    
    with col1:
        prompt = st.chat_input("Ask about insurance claims or savings growth...")
    
    with col2:
        if VOICE_ENABLED:
            if st.button("🎙️", help="Record voice", key="voice_record_btn", use_container_width=False):
                st.session_state.show_voice_recorder = True

# Voice recorder section (hidden by default)
if VOICE_ENABLED and st.session_state.get("show_voice_recorder", False):
    st.divider()
    st.markdown("#### 🎤 Voice Recording")
    
    # Use file uploader for audio recording
    col1, col2 = st.columns([4, 1])
    with col1:
        recorded_audio = st.audio_input("Record or upload audio", label_visibility="collapsed", key="voice_record")
    
    with col2:
        if st.button("✓ Process", key="process_voice"):
            if recorded_audio:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(recorded_audio.getbuffer())
                    temp_audio_path = tmp_file.name
                
                with st.spinner("🔄 Processing..."):
                    lang_code = LANGUAGE_CODES[st.session_state.selected_language]
                    result = process_voice_input(temp_audio_path, lang_code)
                
                if result['success']:
                    st.session_state.messages.append({"role": "user", "content": f"🎤 {result['user_text']}"})
                    st.session_state.messages.append({"role": "assistant", "content": result['response_text']})
                    
                    if result['audio_file']:
                        st.session_state.last_voice_response_audio = result['audio_file']
                    
                    st.session_state.show_voice_recorder = False
                    st.success("✅ Done!")
                    st.rerun()
                else:
                    st.error(f"❌ {result['response_text']}")
                
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
            else:
                st.warning("Please record audio first")

# Voice generation section
if VOICE_ENABLED and st.session_state.get("show_voice_gen", False):
    st.divider()
    st.markdown("#### 🎵 Generate Voice Response")
    
    last_assistant_msg = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant":
            last_assistant_msg = msg
            break
    
    if last_assistant_msg:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.caption(f"Generating in {st.session_state.selected_language}")
        
        with col2:
            if st.button("Generate", key="gen_voice_go"):
                try:
                    lang_code = LANGUAGE_CODES[st.session_state.selected_language]
                    audio_file_output = f"temp_response_{int(time.time())}.mp3"
                    response_text = last_assistant_msg["content"]
                    
                    with st.spinner(f"Converting to voice..."):
                        audio_path = text_to_speech(response_text, audio_file_output, language=lang_code)
                    
                    if audio_path:
                        st.session_state.last_voice_response_audio = audio_path
                        st.session_state.show_voice_gen = False
                        st.success("✅ Voice ready!")
                        st.rerun()
                    else:
                        st.error("Failed to generate voice")
                except Exception as e:
                    logger.error(f"Voice generation error: {str(e)}")
                    st.error(f"Error: {str(e)[:100]}")

# Process text prompt if provided
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = generate_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
