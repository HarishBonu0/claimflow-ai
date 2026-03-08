"""FastAPI backend for ClaimFlow AI.

This module exposes API endpoints for chat, voice, and document features
while keeping existing LLM/RAG business logic intact.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import tempfile
import time
import uuid
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

# Suppress verbose logging from dependencies
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from llm.integration_example import answer_query
from llm.intent_classifier import IntentClassifier
from llm.safety_filter import check_safety
from utils.document_processor import analyze_claim_document, get_document_summary, process_document
from utils.language_detector import detect_language, get_language_name, get_tts_language_code
from voice.stt import speech_to_text_with_retry
from voice.tts import text_to_speech

SUPPORTED_LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
}

LANGUAGE_NAME_BY_CODE = {code: name for name, code in SUPPORTED_LANGUAGES.items()}
OCR_LANG_BY_CODE = {
    "en": "eng",
    "hi": "hin",
    "te": "tel",
    "ta": "tam",
    "kn": "kan",
}


def _load_system_prompt() -> str:
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return (
            "You are ClaimFlow AI, a multilingual insurance assistant. "
            "Respond in the user language (English, Hindi, Telugu, Tamil, Kannada). "
            "Use simple language and step-by-step explanations."
        )


SYSTEM_PROMPT = _load_system_prompt()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    language: str | None = None  # Selected language from frontend


class ChatResponse(BaseModel):
    session_id: str
    response: str
    language: str
    audio_base64: str | None = None
    transcript: str | None = None


class SessionState(BaseModel):
    messages: list[dict[str, str]] = Field(default_factory=list)
    document_text: str = ""
    document_chunks: list[str] = Field(default_factory=list)
    uploaded_document: str | None = None
    last_detected_language: str = "English"


class User(BaseModel):
    email: str
    name: str
    password_hash: str
    created_at: float = Field(default_factory=time.time)


class SignupRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user_email: str | None = None
    user_name: str | None = None
    session_token: str | None = None


sessions: dict[str, SessionState] = {}
users: dict[str, User] = {}  # In production, use a real database
auth_sessions: dict[str, str] = {}  # session_token -> email mapping


app = FastAPI(title="ClaimFlow AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_or_create_session(session_id: str | None) -> tuple[str, SessionState]:
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]

    new_id = str(uuid.uuid4())
    sessions[new_id] = SessionState()
    return new_id, sessions[new_id]


def chunk_document_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if not text:
        return []

    chunks: list[str] = []
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


def retrieve_document_chunks(query: str, document_chunks: list[str], k: int = 3) -> list[str]:
    if not query or not document_chunks:
        return []

    query_terms = {token.lower() for token in query.split() if len(token.strip()) > 2}
    if not query_terms:
        return document_chunks[:k]

    scored: list[tuple[int, str]] = []
    for chunk in document_chunks:
        chunk_terms = {token.lower() for token in chunk.split()}
        overlap_score = len(query_terms.intersection(chunk_terms))
        if overlap_score > 0:
            scored.append((overlap_score, chunk))

    if not scored:
        return document_chunks[:k]

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:k]]


def build_enhanced_prompt(user_input: str, session: SessionState, preferred_language: str | None = None) -> tuple[str, str]:
    # Use preferred language if provided, otherwise detect from input
    if preferred_language:
        # Normalize the language label to code
        lang_code = SUPPORTED_LANGUAGES.get(preferred_language, None)
        if lang_code:
            detected_lang = lang_code
            lang_name = preferred_language
        else:
            # Try to detect if it's already a code
            detected_lang = preferred_language.lower()
            lang_name = LANGUAGE_NAME_BY_CODE.get(detected_lang, preferred_language)
    else:
        # Fall back to detection from message content
        detected_lang, _ = detect_language(user_input)
        detected_lang = get_tts_language_code(detected_lang)
        lang_name = get_language_name(detected_lang)
    
    session.last_detected_language = LANGUAGE_NAME_BY_CODE.get(detected_lang, "English")

    # Enhanced language instruction with transliteration support
    language_instruction = f"""
IMPORTANT LANGUAGE INSTRUCTIONS:
1. The user has selected {lang_name} as their preferred language.
2. You MUST respond ONLY in {lang_name}, regardless of the input language.
3. TRANSLITERATION SUPPORT:
   - If the user writes {lang_name} words using English letters (transliteration),
     recognize the intent and respond in proper {lang_name} script.
   - Examples of transliteration:
     * "claim cheyyatam yelaa" (Telugu in English) → Respond in Telugu script
     * "kaise claim kare" (Hindi in English) → Respond in Hindi script
     * "claim eppadi poduvadhu" (Tamil in English) → Respond in Tamil script
4. Use very simple wording suitable for voice playback and low-literacy users.
5. For procedures, always provide short step-by-step instructions.
6. Do not mention internal system behavior."""

    document_instruction = ""
    if session.document_text:
        top_chunks = retrieve_document_chunks(user_input, session.document_chunks, k=3)
        selected_context = "\n\n".join(top_chunks) if top_chunks else session.document_text[:1000]
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

    return enhanced_query, detected_lang


def generate_chat_response(user_input: str, session: SessionState, preferred_language: str | None = None) -> tuple[str, str]:
    intent, _ = IntentClassifier.classify(user_input)
    is_safe, rejection_message = check_safety(user_input)
    if not is_safe:
        return rejection_message, "en"

    enhanced_query, detected_lang = build_enhanced_prompt(user_input, session, preferred_language)
    
    # Pass conversation history to answer_query for context-aware responses
    response = answer_query(
        enhanced_query, 
        context_k=3, 
        verbose=False,
        conversation_history=session.messages  # Pass full conversation history
    )
    
    if not response:
        response = "I could not generate a response. Please try again."
    return response, detected_lang


def maybe_build_tts_audio(text: str, language_code: str) -> str | None:
    audio_file = f"temp_response_{int(time.time())}.mp3"
    audio_path = text_to_speech(text, audio_file, language=language_code)
    if not audio_path or not os.path.exists(audio_path):
        return None
    with open(audio_path, "rb") as file:
        audio_b64 = base64.b64encode(file.read()).decode("ascii")
    try:
        os.remove(audio_path)
    except OSError:
        pass
    return audio_b64


def parse_preferred_language(preferred_language: str | None) -> str | None:
    """Normalize language label/code/locale to supported ISO code."""
    if not preferred_language:
        return None

    normalized = preferred_language.strip().lower()
    mapping = {
        "english": "en",
        "en": "en",
        "en-in": "en",
        "hindi": "hi",
        "hi": "hi",
        "hi-in": "hi",
        "telugu": "te",
        "te": "te",
        "te-in": "te",
        "tamil": "ta",
        "ta": "ta",
        "ta-in": "ta",
        "kannada": "kn",
        "kn": "kn",
        "kn-in": "kn",
    }
    return mapping.get(normalized)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def init_demo_user():
    """Create a demo user for testing purposes."""
    demo_email = "abc@gmail.com"
    if demo_email not in users:
        users[demo_email] = User(
            email=demo_email,
            name="Demo User",
            password_hash=hash_password("12345678")
        )


# Initialize demo user
init_demo_user()


@app.post("/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest) -> AuthResponse:
    """Register a new user."""
    if request.email in users:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password)
    )
    users[request.email] = user
    
    # Create session token
    session_token = str(uuid.uuid4())
    auth_sessions[session_token] = request.email
    
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user_email=user.email,
        user_name=user.name,
        session_token=session_token
    )


@app.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest) -> AuthResponse:
    """Login an existing user."""
    if request.email not in users:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = users[request.email]
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session token
    session_token = str(uuid.uuid4())
    auth_sessions[session_token] = request.email
    
    return AuthResponse(
        success=True,
        message="Login successful",
        user_email=user.email,
        user_name=user.name,
        session_token=session_token
    )


@app.post("/auth/logout")
def logout(session_token: str = Form(...)) -> dict[str, str]:
    """Logout user and invalidate session token."""
    if session_token in auth_sessions:
        del auth_sessions[session_token]
    return {"message": "Logged out successfully"}


@app.get("/auth/verify")
def verify_session(session_token: str) -> dict[str, Any]:
    """Verify if session token is valid."""
    if session_token not in auth_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    email = auth_sessions[session_token]
    user = users.get(email)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "valid": True,
        "user_email": user.email,
        "user_name": user.name
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id, session = get_or_create_session(request.session_id)

    session.messages.append({"role": "user", "content": request.message})
    response_text, lang_code = generate_chat_response(
        request.message, 
        session,
        preferred_language=request.language  # Pass preferred language
    )
    session.messages.append({"role": "assistant", "content": response_text})

    # Generate TTS audio in the correct language
    audio_base64 = maybe_build_tts_audio(response_text, lang_code)

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        language=LANGUAGE_NAME_BY_CODE.get(lang_code, "English"),
        audio_base64=audio_base64,  # Include audio for voice output
    )


@app.post("/voice", response_model=ChatResponse)
def voice_chat(
    session_id: str | None = Form(default=None),
    preferred_language: str | None = Form(default=None),
    audio: UploadFile = File(...),
) -> ChatResponse:
    session_id, session = get_or_create_session(session_id)

    suffix = os.path.splitext(audio.filename or "voice.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(audio.file.read())
        temp_audio_path = temp_audio.name

    try:
        preferred_lang = (
            parse_preferred_language(preferred_language)
            or SUPPORTED_LANGUAGES.get(session.last_detected_language, "en")
        )
        user_text = speech_to_text_with_retry(temp_audio_path, language=preferred_lang, max_retries=2)
        if user_text.startswith("Error:"):
            preferred_name = LANGUAGE_NAME_BY_CODE.get(preferred_lang, "your selected language")
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not clearly recognize your {preferred_name} voice input. "
                    "Please speak a little slower and try again."
                ),
            )

        session.messages.append({"role": "user", "content": user_text})
        # Pass preferred_language to generate_chat_response for language-specific responses
        response_text, lang_code = generate_chat_response(
            user_text, 
            session,
            preferred_language=preferred_language
        )
        session.messages.append({"role": "assistant", "content": response_text})

        audio_b64 = maybe_build_tts_audio(response_text, lang_code)
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            language=LANGUAGE_NAME_BY_CODE.get(lang_code, "English"),
            audio_base64=audio_b64,
            transcript=user_text,
        )
    finally:
        try:
            os.remove(temp_audio_path)
        except OSError:
            pass


@app.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> dict[str, Any]:
    session_id, session = get_or_create_session(session_id)

    file_name = file.filename or "document"
    extension = os.path.splitext(file_name)[1].lower()
    if extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, and PNG files are supported.")

    file_type = "pdf" if extension == ".pdf" else "image"
    ocr_lang = OCR_LANG_BY_CODE.get(SUPPORTED_LANGUAGES.get(session.last_detected_language, "en"), "eng")

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name

    try:
        result = process_document(temp_path, file_type, ocr_lang=ocr_lang)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to process document."))

    document_text = result.get("text", "")
    analysis = analyze_claim_document(document_text)
    summary = get_document_summary(document_text, max_chars=300)

    session.document_text = document_text
    session.document_chunks = chunk_document_text(document_text)
    session.uploaded_document = file_name

    return {
        "session_id": session_id,
        "file_name": file_name,
        "summary": summary,
        "char_count": len(document_text),
        "analysis": analysis,
    }


@app.get("/history/{session_id}")
def history(session_id: str) -> dict[str, Any]:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "messages": session.messages,
        "last_detected_language": session.last_detected_language,
        "uploaded_document": session.uploaded_document,
    }
