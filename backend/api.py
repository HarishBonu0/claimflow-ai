"""FastAPI backend for ClaimFlow AI.

This module exposes API endpoints for chat, voice, and document features
while keeping existing LLM/RAG business logic intact.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, StrictStr
from psycopg2 import pool
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv
from passlib.context import CryptContext

# Suppress verbose logging from dependencies
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger("claimflow.api")

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

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required. Add Neon PostgreSQL URL to .env")

APP_ENV = os.getenv("APP_ENV", "development").lower()
AUTH_SESSION_HOURS = int(os.getenv("AUTH_SESSION_HOURS", "168"))
RATE_LIMIT_AUTH_PER_MIN = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "20"))
RATE_LIMIT_CHAT_PER_MIN = int(os.getenv("RATE_LIMIT_CHAT_PER_MIN", "60"))
RATE_LIMIT_UPLOAD_PER_MIN = int(os.getenv("RATE_LIMIT_UPLOAD_PER_MIN", "15"))
RATE_LIMIT_VOICE_PER_MIN = int(os.getenv("RATE_LIMIT_VOICE_PER_MIN", "20"))
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "chroma_local")

allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "https://claimflow-ai-bot.vercel.app,http://localhost:5173,http://127.0.0.1:5173",
)
ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

# Log CORS configuration for debugging
logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")
logger.info(f"APP_ENV: {APP_ENV}")

# In development, also allow localhost variations; in production, use strict allowlist
if APP_ENV != "production":
    # Add common localhost aliases for development
    dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    for origin in dev_origins:
        if origin not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(origin)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
argon2_context = CryptContext(schemes=["argon2"], deprecated="auto")
AUTH_HASH_SCHEME = os.getenv("AUTH_HASH_SCHEME", "bcrypt").strip().lower()
AUTH_DEBUG_PASSWORD_LOG = os.getenv("AUTH_DEBUG_PASSWORD_LOG", "false").strip().lower() in {"1", "true", "yes", "on"}


def _log_auth_backend_versions() -> None:
    try:
        passlib_version = version("passlib")
    except PackageNotFoundError:
        passlib_version = "not-installed"

    try:
        bcrypt_version = version("bcrypt")
    except PackageNotFoundError:
        bcrypt_version = "not-installed"

    try:
        argon2_version = version("argon2-cffi")
    except PackageNotFoundError:
        argon2_version = "not-installed"

    logger.info(
        json.dumps(
            {
                "event": "auth_backend_versions",
                "passlib": passlib_version,
                "bcrypt": bcrypt_version,
                "argon2_cffi": argon2_version,
                "auth_hash_scheme": AUTH_HASH_SCHEME,
            }
        )
    )


def _password_debug_payload(password_text: str) -> dict[str, Any]:
    password_bytes = password_text.encode("utf-8")
    payload: dict[str, Any] = {
        "password_type": type(password_text).__name__,
        "password_char_length": len(password_text),
        "password_byte_length": len(password_bytes),
        "password_sha256_12": hashlib.sha256(password_bytes).hexdigest()[:12],
    }
    if AUTH_DEBUG_PASSWORD_LOG:
        payload["password_value"] = password_text
        payload["password_repr"] = repr(password_text)
    return payload

try:
    import sentry_sdk  # type: ignore

    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.05")))
        logger.info("Sentry initialized")
except Exception:
    logger.warning("Sentry SDK not configured or unavailable")

db_pool: pool.SimpleConnectionPool | None = None
rate_limit_state: dict[str, list[float]] = {}
rate_limit_lock = threading.Lock()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    language: str | None = None  # Selected language from frontend
    session_token: str | None = None
    include_audio: bool = False


class ChatResponse(BaseModel):
    session_id: str
    response: str
    language: str
    audio_base64: str | None = None
    transcript: str | None = None
    transcript_translated: str | None = None


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
    password: StrictStr = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user_email: str | None = None
    user_name: str | None = None
    session_token: str | None = None


app = FastAPI(title="ClaimFlow AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(
            json.dumps(
                {
                    "event": "request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                }
            )
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "request_complete",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(request: Request, bucket: str, limit: int, window_seconds: int = 60) -> None:
    now = time.time()
    key = f"{bucket}:{_client_ip(request)}"
    with rate_limit_lock:
        timestamps = rate_limit_state.get(key, [])
        timestamps = [ts for ts in timestamps if now - ts < window_seconds]
        if len(timestamps) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please wait and retry.")
        timestamps.append(now)
        rate_limit_state[key] = timestamps


def get_health_warnings() -> list[str]:
    warnings: list[str] = []

    if APP_ENV == "production" and VECTOR_BACKEND == "chroma_local":
        warnings.append("VECTOR_BACKEND is chroma_local in production. Consider managed vector storage.")

    try:
        import pytesseract

        _ = pytesseract.get_tesseract_version()
    except Exception:
        warnings.append("Tesseract OCR binary not detected. Image document OCR may fail in deployment.")

    return warnings


def init_db_pool() -> None:
    global db_pool
    if db_pool is not None:
        return
    db_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)


@contextmanager
def get_db_conn():
    if db_pool is None:
        init_db_pool()
    assert db_pool is not None
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)


def init_db_schema() -> None:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    session_token TEXT PRIMARY KEY,
                    email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '168 hours')
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id UUID PRIMARY KEY,
                    user_email TEXT REFERENCES users(email) ON DELETE SET NULL,
                    last_detected_language TEXT NOT NULL DEFAULT 'English',
                    document_text TEXT NOT NULL DEFAULT '',
                    document_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
                    uploaded_document TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id BIGSERIAL PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id_id ON chat_messages(session_id, id);"
            )
            cur.execute(
                "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_email TEXT REFERENCES users(email) ON DELETE SET NULL;"
            )
            cur.execute(
                "ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '168 hours');"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_sessions_email_expires ON auth_sessions(email, expires_at DESC);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated ON chat_sessions(user_email, updated_at DESC);"
            )
        conn.commit()


def load_messages(session_id: str) -> list[dict[str, str]]:
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT role, content FROM chat_messages WHERE session_id = %s ORDER BY id ASC",
                (session_id,),
            )
            rows = cur.fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def get_session_state(session_id: str) -> SessionState | None:
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT session_id, last_detected_language, document_text, document_chunks, uploaded_document
                FROM chat_sessions
                WHERE session_id = %s
                """,
                (session_id,),
            )
            row = cur.fetchone()

    if not row:
        return None

    return SessionState(
        messages=load_messages(session_id),
        document_text=row["document_text"] or "",
        document_chunks=row["document_chunks"] or [],
        uploaded_document=row["uploaded_document"],
        last_detected_language=row["last_detected_language"] or "English",
    )


def create_session(user_email: str | None = None) -> tuple[str, SessionState]:
    session_id = str(uuid.uuid4())
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_sessions (session_id, user_email) VALUES (%s, %s)",
                (session_id, user_email),
            )
        conn.commit()
    return session_id, SessionState()


def attach_session_to_user(session_id: str, user_email: str) -> None:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat_sessions
                SET user_email = %s,
                    updated_at = NOW()
                WHERE session_id = %s
                  AND (user_email IS NULL OR user_email = %s)
                """,
                (user_email, session_id, user_email),
            )
        conn.commit()


def upsert_session_state(session_id: str, session: SessionState) -> None:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat_sessions
                SET last_detected_language = %s,
                    document_text = %s,
                    document_chunks = %s,
                    uploaded_document = %s,
                    updated_at = NOW()
                WHERE session_id = %s
                """,
                (
                    session.last_detected_language,
                    session.document_text,
                    Json(session.document_chunks),
                    session.uploaded_document,
                    session_id,
                ),
            )
        conn.commit()


def add_message(session_id: str, role: str, content: str) -> None:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, role, content),
            )
        conn.commit()


def get_user_by_email(email: str) -> User | None:
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT email, name, password_hash, EXTRACT(EPOCH FROM created_at) AS created_at FROM users WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return User(
        email=row["email"],
        name=row["name"],
        password_hash=row["password_hash"],
        created_at=float(row["created_at"]),
    )


def create_user_record(name: str, email: str, password_hash: str) -> User:
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, password_hash)
                VALUES (%s, %s, %s)
                RETURNING email, name, password_hash, EXTRACT(EPOCH FROM created_at) AS created_at
                """,
                (email, name, password_hash),
            )
            row = cur.fetchone()
        conn.commit()
    return User(
        email=row["email"],
        name=row["name"],
        password_hash=row["password_hash"],
        created_at=float(row["created_at"]),
    )


def create_auth_session(email: str) -> str:
    session_token = secrets.token_urlsafe(48)
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO auth_sessions (session_token, email, expires_at)
                VALUES (%s, %s, NOW() + (%s || ' hours')::interval)
                """,
                (session_token, email, AUTH_SESSION_HOURS),
            )
        conn.commit()
    return session_token


def delete_auth_session(session_token: str) -> None:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM auth_sessions WHERE session_token = %s", (session_token,))
        conn.commit()


def delete_all_auth_sessions(email: str) -> None:
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM auth_sessions WHERE email = %s", (email,))
        conn.commit()


def resolve_session_user(session_token: str) -> User | None:
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT u.email, u.name, u.password_hash, EXTRACT(EPOCH FROM u.created_at) AS created_at
                FROM auth_sessions a
                JOIN users u ON u.email = a.email
                WHERE a.session_token = %s
                  AND a.expires_at > NOW()
                """,
                (session_token,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return User(
        email=row["email"],
        name=row["name"],
        password_hash=row["password_hash"],
        created_at=float(row["created_at"]),
    )


def resolve_session_email(session_token: str | None) -> str | None:
    if not session_token:
        return None
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT email FROM auth_sessions WHERE session_token = %s AND expires_at > NOW()",
                (session_token,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return row["email"]


def list_user_sessions(email: str) -> list[dict[str, Any]]:
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    s.session_id::text AS session_id,
                    COALESCE(
                        (SELECT LEFT(m.content, 40)
                         FROM chat_messages m
                         WHERE m.session_id = s.session_id AND m.role = 'user'
                         ORDER BY m.id ASC
                         LIMIT 1),
                        'New Chat'
                    ) AS title,
                    s.updated_at
                FROM chat_sessions s
                WHERE s.user_email = %s
                ORDER BY s.updated_at DESC
                """,
                (email,),
            )
            rows = cur.fetchall()

    result: list[dict[str, Any]] = []
    for row in rows:
        title = row["title"] or "New Chat"
        if len(title) > 40:
            title = f"{title[:40]}..."
        result.append({"id": row["session_id"], "title": title})
    return result


def get_or_create_session(session_id: str | None, user_email: str | None = None) -> tuple[str, SessionState]:
    normalized_session_id: str | None = None
    if session_id:
        try:
            normalized_session_id = str(uuid.UUID(session_id))
        except ValueError:
            normalized_session_id = None

    if normalized_session_id:
        existing = get_session_state(normalized_session_id)
        if existing:
            if user_email:
                attach_session_to_user(normalized_session_id, user_email)
            return normalized_session_id, existing

    return create_session(user_email=user_email)


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


def _language_name_from_preference(preferred_language: str | None) -> tuple[str | None, str | None]:
    """Return normalized language code and display name from label/code/locale."""
    lang_code = parse_preferred_language(preferred_language)
    if not lang_code:
        return None, None
    return lang_code, LANGUAGE_NAME_BY_CODE.get(lang_code, "English")


def translate_transcript_for_language(transcript: str, preferred_language: str | None) -> str:
    """Best-effort translation of voice transcript into user's selected language."""
    if not transcript or not transcript.strip():
        return transcript

    target_code, target_name = _language_name_from_preference(preferred_language)
    if not target_code or not target_name:
        return transcript

    detected_code, _ = detect_language(transcript)
    detected_code = get_tts_language_code(detected_code)
    if detected_code == target_code:
        return transcript

    translation_prompt = (
        f"Translate the following user message to {target_name}. "
        "Return only the translated text with no explanation.\n\n"
        f"Message: {transcript}\n"
        "Translation:"
    )
    translated = answer_query(translation_prompt, context_k=0, verbose=False)
    translated = (translated or "").strip()

    # Fall back to original transcript when translation fails or returns generic service text.
    if not translated:
        return transcript
    lowered = translated.lower()
    if (
        "i'm here to help with insurance questions" in lowered
        or "failed to generate response" in lowered
        or "temporarily unavailable" in lowered
    ):
        return transcript

    return translated


def build_enhanced_prompt(user_input: str, session: SessionState, preferred_language: str | None = None) -> tuple[str, str]:
    # Use preferred language if provided, otherwise detect from input
    if preferred_language:
        normalized_code, normalized_name = _language_name_from_preference(preferred_language)
        if normalized_code and normalized_name:
            detected_lang = normalized_code
            lang_name = normalized_name
        else:
            # Last fallback if caller passed an unknown custom value.
            detected_lang = preferred_language.strip().lower()
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
def health() -> dict[str, Any]:
    warnings = get_health_warnings()
    return {
        "status": "ok",
        "env": APP_ENV,
        "vector_backend": VECTOR_BACKEND,
        "warnings": warnings,
    }


def hash_password(password: str) -> str:
    """Hash password with selected scheme and reliable fallback."""
    password_text = password if isinstance(password, str) else str(password)
    password_bytes = password_text.encode("utf-8")

    logger.info(
        json.dumps(
            {
                "event": "hash_password_input",
                **_password_debug_payload(password_text),
            }
        )
    )

    if AUTH_HASH_SCHEME == "argon2":
        return argon2_context.hash(password_text)

    # Avoid bcrypt's 72-byte hard limit by using argon2 for long UTF-8 byte payloads.
    if len(password_bytes) > 72:
        return argon2_context.hash(password_text)

    try:
        return pwd_context.hash(password_text)
    except Exception as exc:
        logger.warning(f"bcrypt hash failed, falling back to argon2: {type(exc).__name__}: {exc}")
        return argon2_context.hash(password_text)


def sanitize_password_input(password: str) -> str:
    """Normalize accidental formatting/hidden chars from client payload."""
    if not isinstance(password, str):
        raise HTTPException(status_code=400, detail="Password must be sent as a plain string")

    normalized = password

    # Recover from accidental JSON.stringify(password) value like "\"secret\"".
    if normalized.startswith('"') and normalized.endswith('"'):
        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, str):
                normalized = parsed
        except json.JSONDecodeError:
            pass

    # Strip hidden Unicode chars that may alter effective byte length.
    hidden_chars = {ord("\u200b"): None, ord("\u200c"): None, ord("\u200d"): None, ord("\u2060"): None, ord("\ufeff"): None}
    normalized = normalized.translate(hidden_chars)

    if "\x00" in normalized:
        raise HTTPException(status_code=400, detail="Password contains invalid control characters")

    return normalized


def validate_signup_password(password: str) -> None:
    """Validate password constraints before hashing."""
    if not isinstance(password, str):
        raise HTTPException(status_code=400, detail="Password must be sent as a plain string")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if len(password) > 1024:
        raise HTTPException(status_code=400, detail="Password too long")
    password_byte_length = len(password.encode("utf-8"))
    if password_byte_length > 4096:
        raise HTTPException(status_code=400, detail="Password byte length too large")

    logger.info(
        json.dumps(
            {
                "event": "signup_password_validated",
                **_password_debug_payload(password),
            }
        )
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    password_text = password if isinstance(password, str) else str(password)
    try:
        if isinstance(password_hash, str) and password_hash.startswith("$argon2"):
            return argon2_context.verify(password_text, password_hash)
        if AUTH_HASH_SCHEME == "argon2":
            return argon2_context.verify(password_text, password_hash)
        return pwd_context.verify(password_text, password_hash)
    except Exception as exc:
        logger.warning(f"Password verification failed: {type(exc).__name__}: {exc}")
        try:
            if isinstance(password_hash, str) and password_hash.startswith("$2"):
                return pwd_context.verify(password_text, password_hash)
            if isinstance(password_hash, str) and password_hash.startswith("$argon2"):
                return argon2_context.verify(password_text, password_hash)
        except Exception:
            pass
        return False


def init_demo_user():
    """Create a demo user for testing purposes."""
    demo_email = "abc@gmail.com"
    if not get_user_by_email(demo_email):
        create_user_record(
            name="Demo User",
            email=demo_email,
            password_hash=hash_password("12345678"),
        )


@app.on_event("startup")
def startup_event() -> None:
    _log_auth_backend_versions()
    init_db_pool()
    init_db_schema()
    init_demo_user()


@app.post("/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest, req: Request) -> AuthResponse:
    """Register a new user."""
    try:
        enforce_rate_limit(req, "auth_signup", RATE_LIMIT_AUTH_PER_MIN)
        
        logger.info(f"Signup attempt for email: {request.email}")
        
        # Check if email already exists
        existing_user = get_user_by_email(request.email)
        if existing_user:
            logger.info(f"Signup failed: Email already registered - {request.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        password = sanitize_password_input(request.password)
        logger.info(
            json.dumps(
                {
                    "event": "signup_password_received",
                    "email": request.email,
                    **_password_debug_payload(password),
                }
            )
        )
        validate_signup_password(password)
        
        # Create user
        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            logger.warning(f"Signup failed: Invalid password input for {request.email}: {exc}")
            raise HTTPException(status_code=400, detail="Invalid password format") from exc

        user = create_user_record(
            name=request.name,
            email=request.email,
            password_hash=password_hash,
        )
        
        # Create session token
        session_token = create_auth_session(user.email)
        
        logger.info(f"User created successfully: {user.email}")
        
        return AuthResponse(
            success=True,
            message="Account created successfully",
            user_email=user.email,
            user_name=user.name,
            session_token=session_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Signup failed due to a server error. Please try again.")


@app.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, req: Request) -> AuthResponse:
    """Login an existing user."""
    try:
        enforce_rate_limit(req, "auth_login", RATE_LIMIT_AUTH_PER_MIN)
        
        logger.info(f"Login attempt for email: {request.email}")
        
        # Look up user
        user = get_user_by_email(request.email)
        if not user:
            logger.warning(f"Login failed: User not found - {request.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"Login failed: Invalid password - {request.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create session token
        session_token = create_auth_session(user.email)
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return AuthResponse(
            success=True,
            message="Login successful",
            user_email=user.email,
            user_name=user.name,
            session_token=session_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed due to a server error. Please try again.")


@app.post("/auth/logout")
def logout(request: Request, session_token: str = Form(...)) -> dict[str, str]:
    """Logout user and invalidate session token."""
    enforce_rate_limit(request, "auth_logout", RATE_LIMIT_AUTH_PER_MIN)
    delete_auth_session(session_token)
    return {"message": "Logged out successfully"}


@app.get("/auth/verify")
def verify_session(session_token: str) -> dict[str, Any]:
    """Verify if session token is valid."""
    user = resolve_session_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "valid": True,
        "user_email": user.email,
        "user_name": user.name
    }


@app.post("/auth/revoke-all")
def revoke_all_sessions(request: Request, session_token: str = Form(...)) -> dict[str, str]:
    enforce_rate_limit(request, "auth_revoke_all", RATE_LIMIT_AUTH_PER_MIN)
    user = resolve_session_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    delete_all_auth_sessions(user.email)
    return {"message": "All sessions revoked successfully"}


@app.get("/sessions")
def sessions_list(session_token: str) -> dict[str, Any]:
    user = resolve_session_user(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"sessions": list_user_sessions(user.email)}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, req: Request) -> ChatResponse:
    enforce_rate_limit(req, "chat", RATE_LIMIT_CHAT_PER_MIN)
    try:
        user_email = resolve_session_email(request.session_token)
        session_id, session = get_or_create_session(request.session_id, user_email=user_email)

        session.messages.append({"role": "user", "content": request.message})
        add_message(session_id, "user", request.message)
        response_text, lang_code = generate_chat_response(
            request.message,
            session,
            preferred_language=request.language,
        )
        session.messages.append({"role": "assistant", "content": response_text})
        add_message(session_id, "assistant", response_text)
        upsert_session_state(session_id, session)

        # For typed chat, generate voice output only when explicitly requested.
        audio_base64 = maybe_build_tts_audio(response_text, lang_code) if request.include_audio else None

        return ChatResponse(
            session_id=session_id,
            response=response_text,
            language=LANGUAGE_NAME_BY_CODE.get(lang_code, "English"),
            audio_base64=audio_base64,
        )
    except Exception as error:
        logger.exception("chat_endpoint_error: %s", error)
        fallback_session_id = request.session_id
        try:
            fallback_session_id = str(uuid.UUID(request.session_id)) if request.session_id else str(uuid.uuid4())
        except Exception:
            fallback_session_id = str(uuid.uuid4())

        return ChatResponse(
            session_id=fallback_session_id,
            response=(
                "I am having trouble completing your request right now. "
                "Please try again in a few seconds."
            ),
            language=request.language if request.language in SUPPORTED_LANGUAGES else "English",
            audio_base64=None,
        )


@app.post("/voice", response_model=ChatResponse)
@app.post("/voice-input", response_model=ChatResponse)
def voice_chat(
    req: Request,
    session_id: str | None = Form(default=None),
    preferred_language: str | None = Form(default=None),
    session_token: str | None = Form(default=None),
    audio: UploadFile = File(...),
) -> ChatResponse:
    enforce_rate_limit(req, "voice", RATE_LIMIT_VOICE_PER_MIN)
    user_email = resolve_session_email(session_token)
    session_id, session = get_or_create_session(session_id, user_email=user_email)

    suffix = os.path.splitext(audio.filename or "voice.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(audio.file.read())
        temp_audio_path = temp_audio.name

    try:
        preferred_lang = (
            parse_preferred_language(preferred_language)
            or SUPPORTED_LANGUAGES.get(session.last_detected_language, "en")
        )
        preferred_name = LANGUAGE_NAME_BY_CODE.get(preferred_lang, "English")
        logger.info(
            "voice_request_received session_id=%s preferred_language_raw=%s preferred_lang_code=%s preferred_lang_name=%s audio_filename=%s content_type=%s",
            session_id,
            preferred_language,
            preferred_lang,
            preferred_name,
            audio.filename,
            audio.content_type,
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

        translated_transcript = translate_transcript_for_language(user_text, preferred_language)

        session.messages.append({"role": "user", "content": user_text})
        add_message(session_id, "user", user_text)
        # Pass preferred_language to generate_chat_response for language-specific responses
        response_text, lang_code = generate_chat_response(
            user_text, 
            session,
            preferred_language=preferred_language
        )
        session.messages.append({"role": "assistant", "content": response_text})
        add_message(session_id, "assistant", response_text)
        upsert_session_state(session_id, session)

        audio_b64 = maybe_build_tts_audio(response_text, lang_code)
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            language=LANGUAGE_NAME_BY_CODE.get(lang_code, "English"),
            audio_base64=audio_b64,
            transcript=user_text,
            transcript_translated=translated_transcript,
        )
    finally:
        try:
            os.remove(temp_audio_path)
        except OSError:
            pass


@app.post("/upload")
@app.post("/upload-document")
def upload_document(
    req: Request,
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    session_token: str | None = Form(default=None),
) -> dict[str, Any]:
    enforce_rate_limit(req, "upload", RATE_LIMIT_UPLOAD_PER_MIN)
    user_email = resolve_session_email(session_token)
    session_id, session = get_or_create_session(session_id, user_email=user_email)

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
    upsert_session_state(session_id, session)

    return {
        "session_id": session_id,
        "file_name": file_name,
        "summary": summary,
        "char_count": len(document_text),
        "analysis": analysis,
    }


@app.get("/history/{session_id}")
def history(session_id: str) -> dict[str, Any]:
    session = get_session_state(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "messages": session.messages,
        "last_detected_language": session.last_detected_language,
        "uploaded_document": session.uploaded_document,
    }
