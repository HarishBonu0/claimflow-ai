"""
ClaimFlow AI - Insurance Claims & Financial Literacy Assistant
Multilingual Voice-Enabled Interface with Document Understanding
"""

import streamlit as st
import time
import logging
import os
import sys
import tempfile
from datetime import datetime

# Ensure project root is in Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load system prompt
try:
    with open('system_prompt.md', 'r', encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    logger.warning("system_prompt.md not found. Using default prompt.")
    SYSTEM_PROMPT = """You are ClaimFlow AI, a multilingual insurance assistant. 
    Respond in the user's language (English, Hindi, Telugu, Tamil, or Kannada).
    Use simple language, step-by-step explanations, and avoid complex legal terms."""

# Import integration layer and safety modules
from llm.integration_example import answer_query
from llm.safety_filter import check_safety
from llm.intent_classifier import IntentClassifier

# Import language detection (required for multilingual response behavior)
from utils.language_detector import detect_language, get_language_name, get_tts_language_code

# Import document processing (optional)
try:
    from utils.document_processor import process_document, analyze_claim_document, get_document_summary
    DOCUMENT_PROCESSING_ENABLED = True
except ImportError:
    logger.warning("Document processing modules not available. Document features disabled.")
    DOCUMENT_PROCESSING_ENABLED = False

# Import voice modules
try:
    from voice.stt import speech_to_text
    from voice.tts import text_to_speech, play_audio
    VOICE_ENABLED = True
except ImportError:
    logger.warning("Voice modules not available. Voice features disabled.")
    VOICE_ENABLED = False

# Supported language mapping (project scope)
LANGUAGE_CODES = {
    'English': 'en',
    'Hindi': 'hi',
    'Telugu': 'te',
    'Tamil': 'ta',
    'Kannada': 'kn',
}

LANGUAGE_NAME_BY_CODE = {code: name for name, code in LANGUAGE_CODES.items()}

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="ClaimFlow AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# UI-only state via query params (does not affect chatbot/session logic)
sidebar_collapsed = st.query_params.get("sb", "0") == "1"
collapsed_sidebar_css = """
    [data-testid=\"stSidebar\"] {{
        min-width: 4.5rem !important;
        max-width: 4.5rem !important;
    }}

    [data-testid=\"stSidebar\"] .stSelectbox,
    [data-testid=\"stSidebar\"] [data-testid=\"stCaptionContainer\"],
    [data-testid=\"stSidebar\"] h3 {{
        display: none;
    }}
""" if sidebar_collapsed else ""

# ============================================
# CUSTOM CSS - SAFE SAAS DASHBOARD LAYOUT
# ============================================
st.markdown(
    f"""
<style>
    :root {{
        --sidebar-width: {'4.5rem' if sidebar_collapsed else '21rem'};
    }}

    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background: radial-gradient(circle at top left, #0f172a 0%, #020617 70%);
        color: #e2e8f0;
    }}

    .block-container {{
        max-width: 100%;
        padding: 1rem 1.2rem 8.5rem 1.2rem;
    }}

    [data-testid="stSidebar"] {{
        background: #020617;
        border-right: 1px solid rgba(148, 163, 184, 0.22);
    }}

    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background: #0f172a;
        color: #e2e8f0;
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 12px;
    }}

    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {{
        color: #cbd5e1 !important;
    }}

    {collapsed_sidebar_css}

    .chat-shell {{
        max-width: 980px;
        margin: 0 auto;
        background: rgba(15, 23, 42, 0.82);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 18px;
        padding: 1rem 1rem 1.2rem 1rem;
        min-height: calc(100vh - 170px);
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }}

    .chat-header {{
        padding: 0.5rem 0.6rem 1rem 0.6rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        margin-bottom: 1rem;
    }}

    .chat-title {{
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        color: #f8fafc;
    }}

    .chat-subtitle {{
        margin: 0.2rem 0 0.5rem 0;
        color: #cbd5e1;
        font-size: 0.95rem;
    }}

    .chat-helper {{
        margin: 0;
        color: #94a3b8;
        font-size: 0.9rem;
    }}

    .prompt-row {{
        margin-bottom: 0.25rem;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(2, 6, 23, 0.22);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 14px;
    }}

    [data-testid="stChatMessage"] {{
        margin-bottom: 1rem;
    }}

    [data-testid="stChatMessage"][aria-label*="assistant" i] [data-testid="stChatMessageContent"] {{
        margin-right: auto;
        max-width: 70%;
        background: rgba(30, 41, 59, 0.95);
        color: #f8fafc;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 0.7rem 0.9rem;
        line-height: 1.55;
    }}

    [data-testid="stChatMessage"][aria-label*="assistant" i] [data-testid="stMarkdownContainer"] * {{
        color: #f8fafc !important;
    }}

    [data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stChatMessageContent"] {{
        margin-left: auto;
        max-width: 70%;
        background: #e2e8f0;
        color: #0f172a;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        padding: 0.7rem 0.9rem;
        line-height: 1.55;
    }}

    [data-testid="stChatMessage"][aria-label*="user" i] [data-testid="stMarkdownContainer"] * {{
        color: #0f172a !important;
        font-weight: 600;
    }}

    .prompt-row .stButton > button {{
        width: 100%;
        border-radius: 999px;
        background: #111827;
        color: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.35);
        font-weight: 600;
        opacity: 1 !important;
    }}

    .prompt-row .stButton > button:hover {{
        border-color: #22d3ee;
    }}

    button[key^="prompt_"] {{
        border-radius: 999px !important;
        background: #111827 !important;
        color: #ffffff !important;
        border: 1px solid rgba(148, 163, 184, 0.35) !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }}

    button[key^="prompt_"]:hover {{
        border-color: #22d3ee !important;
        box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.3);
    }}

    button[kind="secondary"],
    button[kind="primary"] {{
        cursor: pointer !important;
    }}

    [data-testid="stChatInput"] {{
        position: fixed;
        left: calc(var(--sidebar-width) + 1rem);
        right: 4.8rem;
        bottom: 1rem;
        z-index: 50;
        margin: 0 !important;
        padding: 0 !important;
    }}

    [data-testid="stChatInput"] > div {{
        background: #0f172a;
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 14px;
    }}

    [data-testid="stChatInput"] input {{
        color: #e2e8f0;
    }}

    [data-testid="stChatInput"] input::placeholder {{
        color: #94a3b8;
    }}

    button[key="voice_record_btn"],
    button[key="doc_upload_btn"] {{
        position: fixed;
        bottom: 1rem;
        z-index: 60;
        border-radius: 999px !important;
        height: 44px;
        width: 44px;
        border: 1px solid rgba(148, 163, 184, 0.35) !important;
        background: #0f172a !important;
        color: #e2e8f0 !important;
    }}

    button[key="voice_record_btn"] {{
        right: 1rem;
    }}

    button[key="doc_upload_btn"] {{
        right: 4.2rem;
    }}

    button[key="voice_record_btn"]:hover,
    button[key="doc_upload_btn"]:hover {{
        border-color: #22d3ee !important;
    }}

    [data-testid="stChatMessageContent"] {{
        font-size: 1rem;
    }}

    @media (max-width: 1024px) {{
        button[key="doc_upload_btn"] {{
            right: 4rem;
        }}

        button[key="voice_record_btn"] {{
            right: 0.8rem;
        }}
    }}

    @media (max-width: 640px) {{
        [data-testid="stChatInput"] {{
            right: 6.8rem;
        }}
    }}

    @media (max-width: 1024px) {{
        [data-testid="stChatInput"] {{
            left: 0.8rem;
            right: 4.8rem;
        }}

        .chat-shell {{
            min-height: calc(100vh - 150px);
        }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

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

# Document processing state
if "uploaded_document" not in st.session_state:
    st.session_state.uploaded_document = None

if "document_text" not in st.session_state:
    st.session_state.document_text = ""

if "document_chunks" not in st.session_state:
    st.session_state.document_chunks = []

if "document_analysis" not in st.session_state:
    st.session_state.document_analysis = None

if "show_document_upload" not in st.session_state:
    st.session_state.show_document_upload = False

if "last_detected_language" not in st.session_state:
    st.session_state.last_detected_language = 'English'

# ============================================
# VOICE PROCESSING FUNCTIONS
# ============================================

def process_voice_input(audio_file, language_code):
    """
    Process voice input: convert to text and generate response.
    Supports multilingual speech recognition.
    
    Args:
        audio_file: Path to audio file
        language_code: Language code for STT input AND TTS output (e.g., 'en', 'hi', 'te')
    
    Returns:
        Dictionary with user_text, response_text, and audio_file
    """
    try:
        logger.info("Starting voice input processing...")
        logger.info(f"Voice language: {language_code}")
        
        # Step 1: Speech to text with retry (retry once)
        language_name = LANGUAGE_NAME_BY_CODE.get(language_code, 'English')
        
        logger.info(f"Converting speech to text ({language_name})...")
        
        # Try speech-to-text with retry logic
        try:
            from voice.stt import speech_to_text_with_retry
            user_text = speech_to_text_with_retry(audio_file, language=language_name, max_retries=1)
        except ImportError:
            # Fallback to simple speech_to_text without retry
            user_text = speech_to_text(audio_file, language=language_name, auto_detect=False)
        
        if user_text.startswith("Error:"):
            logger.error(f"STT failed: {user_text}")
            return {
                'user_text': '',
                'response_text': 'Sorry, I could not understand your speech after retrying. Please try again.',
                'audio_file': None,
                'success': False
            }
        
        logger.info(f"Transcribed text: {user_text[:100]}...")
        
        # Keep language consistent with the user's spoken query.
        detected_lang, _ = detect_language(user_text)
        detected_lang = get_tts_language_code(detected_lang)
        st.session_state.selected_language = LANGUAGE_NAME_BY_CODE.get(detected_lang, 'English')
        st.session_state.last_detected_language = st.session_state.selected_language

        # Step 2: Generate response (using text pipeline with document context if available)
        doc_context = st.session_state.document_text if hasattr(st.session_state, 'document_text') else None
        response_text = generate_response(user_text, document_context=doc_context)
        logger.info(f"Generated response: {len(response_text)} characters")
        
        # Step 3: Text to Speech (using selected language)
        logger.info(f"Converting response to speech ({st.session_state.selected_language})...")
        audio_file_output = f"temp_response_{int(time.time())}.mp3"
        audio_path = text_to_speech(response_text, audio_file_output, language=detected_lang)
        
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
            'response_text': 'Voice processing failed. Please try again.',
            'audio_file': None,
            'success': False
        }

def process_document_upload(uploaded_file, ocr_language='eng'):
    """
    Process uploaded document (PDF or image) and extract text.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        ocr_language: OCR language code (eng, hin, tel, tam, kan)
    
    Returns:
        Dictionary with extracted text and analysis
    """
    try:
        logger.info(f"Processing uploaded document: {uploaded_file.name}")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            temp_file_path = tmp_file.name
        
        # Determine file type
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension == '.pdf':
            file_type = 'pdf'
        elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            file_type = 'image'
        else:
            return {
                'success': False,
                'error': f'Unsupported file type: {file_extension}',
                'text': '',
                'analysis': None
            }
        
        # Extract text
        result = process_document(temp_file_path, file_type, ocr_lang=ocr_language)
        
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        if not result['success']:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'text': '',
                'analysis': None
            }
        
        # Analyze document for claim information
        document_text = result['text']
        analysis = analyze_claim_document(document_text)
        
        logger.info(f"Document processed successfully: {len(document_text)} characters")
        
        return {
            'success': True,
            'text': document_text,
            'analysis': analysis,
            'file_name': uploaded_file.name,
            'file_type': file_type,
            'char_count': result.get('char_count', len(document_text))
        }
    
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Error processing document: {str(e)[:100]}',
            'text': '',
            'analysis': None
        }


def chunk_document_text(text, chunk_size=900, overlap=150):
    """Split uploaded document text into reusable chunks for retrieval."""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = max(0, end - overlap)
    return chunks


def retrieve_document_chunks(query, document_chunks, k=3):
    """Return top-k relevant chunks from uploaded documents using token overlap scoring."""
    if not query or not document_chunks:
        return []

    query_terms = {token.lower() for token in query.split() if len(token.strip()) > 2}
    if not query_terms:
        return document_chunks[:k]

    scored = []
    for chunk in document_chunks:
        chunk_terms = {token.lower() for token in chunk.split()}
        overlap = len(query_terms.intersection(chunk_terms))
        if overlap > 0:
            scored.append((overlap, chunk))

    if not scored:
        return document_chunks[:k]

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:k]]

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_response(user_input, document_context=None):
    """
    Generate AI response with safety checks, language detection, and intent classification.
    Optionally includes document context for document-aware responses.
    """
    try:
        logger.info(f"Processing query: {user_input[:50]}...")
        
        # Detect user's language and keep UI voice language aligned.
        detected_lang, confidence = detect_language(user_input)
        detected_lang = get_tts_language_code(detected_lang)
        lang_name = get_language_name(detected_lang)
        st.session_state.selected_language = LANGUAGE_NAME_BY_CODE.get(detected_lang, 'English')
        st.session_state.last_detected_language = st.session_state.selected_language
        logger.info(f"Detected language: {lang_name} ({detected_lang}, confidence: {confidence:.2f})")
        
        # Step 1: Intent classification
        intent, confidence = IntentClassifier.classify(user_input)
        logger.info(f"Intent: {intent} (confidence: {confidence:.2f})")
        
        # Step 2: Safety check (pre-LLM guardrails)
        is_safe, rejection_message = check_safety(user_input)
        if not is_safe:
            logger.warning(f"Query blocked by safety filter: {intent}")
            return rejection_message
        
        # Step 3: Prepare enhanced query with system prompt and language context
        language_instruction = f"""
    IMPORTANT: The user is asking in {lang_name}.
    You must respond in {lang_name} only.
    Use very simple wording suitable for voice playback and low-literacy users.
    For procedures, always provide short step-by-step instructions.
    Do not mention internal system behavior."""
        
        document_instruction = ""
        if document_context:
            chunks = st.session_state.get('document_chunks', [])
            top_chunks = retrieve_document_chunks(user_input, chunks, k=3) if chunks else [document_context[:1000]]
            selected_context = "\n\n".join(top_chunks)
            logger.info(f"Adding retrieved document context ({len(selected_context)} chars)")
            document_instruction = f"""

DOCUMENT CONTEXT:
The user has uploaded an insurance-related document.
Use only the retrieved snippets below when citing document details.

---DOCUMENT START---
{selected_context[:3000]}
---DOCUMENT END---

When answering, reference specific information from the document snippets."""
        
        enhanced_query = f"""{SYSTEM_PROMPT}

---

{language_instruction}{document_instruction}

---

USER QUESTION: {user_input}"""
        
        # Step 4: Use proper integration layer (RAG + LLM)
        response = answer_query(enhanced_query, context_k=3, verbose=False)
        logger.info(f"Response generated: {len(response)} characters in {lang_name}")
        
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
# SIDEBAR
# ============================================
with st.sidebar:
    # Sidebar collapse toggle using query params to avoid backend/session impact.
    if st.button("➡️" if sidebar_collapsed else "⬅️", key="sidebar_toggle", use_container_width=True):
        st.query_params["sb"] = "0" if sidebar_collapsed else "1"
        st.rerun()

    if not sidebar_collapsed:
        st.markdown("### Language")
        st.caption(f"Auto-detected: {st.session_state.last_detected_language}")
        st.caption("Responses stay in the same language as your query.")
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Language support info
    if not sidebar_collapsed:
        with st.expander("🌍 Supported Languages", expanded=False):
            st.markdown("""
            **ClaimFlow AI supports:**
            
            🇮🇳 **Indian Languages**
            - 🔤 हिंदी (Hindi)
            - 🔤 తెలుగు (Telugu)
            - 🔤 தமிழ் (Tamil)
            - 🔤 ಕನ್ನಡ (Kannada)
            
            - 🇬🇧 English
            
            **Auto-detects your language**
            Speak or type in English, Hindi, Telugu, Tamil, or Kannada.
            """)
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    if not sidebar_collapsed:
        st.markdown("### Chat History")
    
    # New Chat Button
    if st.button("➕" if sidebar_collapsed else "➕ New Chat", key="new_chat", use_container_width=True):
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
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Chat History List
    if st.session_state.chat_history:
        for idx, chat in enumerate(st.session_state.chat_history):
            col1, col2 = st.columns([4, 1])
            with col1:
                chat_label = f"💬 {idx + 1}" if sidebar_collapsed else chat["title"]
                if st.button(chat_label, key=f"chat_{chat['id']}", use_container_width=True):
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
        if not sidebar_collapsed:
            st.markdown("<p style='color: #64748b; text-align: center; padding: 1.4rem 1rem; font-size: 0.85rem;'>No previous chats</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Clear All Button
    if st.session_state.chat_history:
        if st.button("🧹" if sidebar_collapsed else "🗑️ Clear All Chats", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.messages = []
            st.session_state.current_chat_id = None
            st.rerun()

    if not sidebar_collapsed:
        st.markdown("<div style='margin-top: auto; padding-top: 1.5rem;'>", unsafe_allow_html=True)
        st.markdown("<p style='color: #475569; font-size: 0.75rem;'>Version 1.0.0</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# MAIN CHAT AREA
# ============================================
st.markdown("""
<div class='chat-shell'>
    <div class='chat-header'>
        <h1 class='chat-title'>ClaimFlow AI</h1>
        <p class='chat-subtitle'>🌍 Multilingual Insurance Assistant</p>
        <p class='chat-helper'>Ask in English, Hindi, Telugu, Tamil, or Kannada • Upload documents • Get instant help</p>
    </div>
""", unsafe_allow_html=True)

# Suggested Prompts
st.markdown("<div class='prompt-row'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("📋 Claim Process Steps", key="prompt_claim_stages", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Explain claim stages in simple steps"})
        st.rerun()
with col2:
    if st.button("⏳ Claim Delay Reasons", key="prompt_claim_delay", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Why is my claim delayed"})
        st.rerun()

col3, col4 = st.columns(2)
with col3:
    if st.button("📄 Required Documents", key="prompt_required_docs", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "What documents are needed for filing a claim"})
        st.rerun()

with col4:
    if st.button("🎯 Ask in Your Language", key="prompt_lang_help", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Can you help me in my local language?"})
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# Display Chat Messages in scrollable container
messages_container = st.container(height=540, border=False)
with messages_container:
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
            st.markdown(f"<p style='color: #64748b; font-size: 0.75rem;'>Language: {st.session_state.selected_language}</p>", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error playing audio: {str(e)}")
        st.warning(f"Could not load voice response: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# CHAT INPUT with VOICE & DOCUMENTS
# ============================================

# Create a container for input controls
input_container = st.container()

with input_container:
    # Adjust columns based on enabled features
    if VOICE_ENABLED and DOCUMENT_PROCESSING_ENABLED:
        col1, col2, col3 = st.columns([1, 0.08, 0.08], gap="small")
    elif VOICE_ENABLED or DOCUMENT_PROCESSING_ENABLED:
        col1, col2 = st.columns([1, 0.08], gap="small")
    else:
        col1 = st.container()
        col2 = None
        col3 = None
    
    with col1:
        prompt = st.chat_input("Ask about insurance claims or upload documents...")
    
    if VOICE_ENABLED and DOCUMENT_PROCESSING_ENABLED:
        with col2:
            if st.button("🎙️", help="Record voice", key="voice_record_btn", use_container_width=False):
                st.session_state.show_voice_recorder = True
                st.session_state.show_document_upload = False
        
        with col3:
            if st.button("📄", help="Upload document", key="doc_upload_btn", use_container_width=False):
                st.session_state.show_document_upload = True
                st.session_state.show_voice_recorder = False
    
    elif VOICE_ENABLED:
        with col2:
            if st.button("🎙️", help="Record voice", key="voice_record_btn", use_container_width=False):
                st.session_state.show_voice_recorder = True
    
    elif DOCUMENT_PROCESSING_ENABLED:
        with col2:
            if st.button("📄", help="Upload document", key="doc_upload_btn", use_container_width=False):
                st.session_state.show_document_upload = True

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

# Document upload section (hidden by default)
if DOCUMENT_PROCESSING_ENABLED and st.session_state.get("show_document_upload", False):
    st.divider()
    st.markdown("#### 📄 Upload Document")
    st.caption("Upload claim documents, bills, medical records, or insurance policies (PDF or images)")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Drop file here",
            type=['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'],
            key="document_uploader",
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("✓ Process", key="process_document"):
            if uploaded_file:
                with st.spinner("🔄 Extracting text from document..."):
                    # Determine OCR language based on selected language
                    ocr_lang_map = {
                        'English': 'eng',
                        'Hindi': 'hin',
                        'Telugu': 'tel',
                        'Tamil': 'tam',
                        'Kannada': 'kan',
                    }
                    ocr_lang = ocr_lang_map.get(st.session_state.selected_language, 'eng')
                    
                    result = process_document_upload(uploaded_file, ocr_language=ocr_lang)
                
                if result['success']:
                    # Store document text
                    st.session_state.document_text = result['text']
                    st.session_state.document_chunks = chunk_document_text(result['text'])
                    st.session_state.document_analysis = result['analysis']
                    st.session_state.uploaded_document = result['file_name']
                    
                    # Show summary
                    st.success(f"✅ Document processed: {result['file_name']}")
                    st.info(f"📊 Extracted {result['char_count']:,} characters")
                    
                    # Display document analysis
                    analysis = result['analysis']
                    if analysis:
                        with st.expander("📋 Document Analysis", expanded=True):
                            st.write(f"**Type:** {analysis['document_type'].replace('_', ' ').title()}")
                            
                            if analysis.get('detected_amounts'):
                                st.write(f"**Amounts:** {', '.join(analysis['detected_amounts'])}")
                            
                            if analysis.get('detected_dates'):
                                st.write(f"**Dates:** {', '.join(analysis['detected_dates'])}")
                            
                            if analysis.get('missing_info'):
                                st.warning(f"⚠️ **Potentially Missing:** {', '.join(analysis['missing_info'])}")
                    
                    # Add to messages
                    summary = get_document_summary(result['text'], max_chars=300)
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📄 **Uploaded document:** {result['file_name']}\n\n**Summary:**\n{summary}"
                    })
                    
                    # Generate automatic analysis
                    auto_prompt = f"Analyze this {analysis['document_type'].replace('_', ' ')} and provide insights on completeness and next steps."
                    response = generate_response(auto_prompt, document_context=result['text'])
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    st.session_state.show_document_upload = False
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
            else:
                st.warning("Please upload a file first")
    
    # Show current document if any
    if st.session_state.document_text:
        st.markdown("---")
        st.markdown(f"**Currently loaded:** {st.session_state.get('uploaded_document', 'Document')}")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📖 View Full Text", key="view_doc_text"):
                with st.expander("Document Text", expanded=True):
                    st.text_area("", st.session_state.document_text, height=300, label_visibility="collapsed")
        with col_b:
            if st.button("🗑️ Clear Document", key="clear_doc"):
                st.session_state.document_text = ""
                st.session_state.document_chunks = []
                st.session_state.document_analysis = None
                st.session_state.uploaded_document = None
                st.success("Document cleared")
                st.rerun()

# Process text prompt if provided
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Use document context if available
    doc_context = st.session_state.document_text if st.session_state.document_text else None
    response = generate_response(prompt, document_context=doc_context)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
