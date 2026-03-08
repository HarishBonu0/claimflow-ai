"""Language detection utilities for ClaimFlow AI.

This module intentionally constrains detection to the product-supported languages:
English, Hindi, Telugu, Tamil, and Kannada.
"""

import logging

logger = logging.getLogger(__name__)

SUPPORTED_CODES = {"en", "hi", "te", "ta", "kn"}

SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari
    "te": (0x0C00, 0x0C7F),  # Telugu
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "kn": (0x0C80, 0x0CFF),  # Kannada
}

LANGUAGE_NAME_MAP = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
}


def _detect_from_script(text: str) -> tuple[str, float] | None:
    """Use Unicode script ranges for highly reliable detection on Indic text."""
    for ch in text:
        codepoint = ord(ch)
        for lang_code, (start, end) in SCRIPT_RANGES.items():
            if start <= codepoint <= end:
                return (lang_code, 0.99)
    return None


def _normalize_detected_code(lang_code: str) -> str:
    """Normalize detector variants to supported language codes."""
    normalized = (lang_code or "").strip().lower()
    alias_map = {
        "en-us": "en",
        "en-gb": "en",
        "hin": "hi",
        "tel": "te",
        "tam": "ta",
        "kan": "kn",
    }
    normalized = alias_map.get(normalized, normalized)
    if normalized in SUPPORTED_CODES:
        return normalized
    return "en"


def detect_language(text: str) -> tuple[str, float]:
    """Detect language and return (supported_lang_code, confidence)."""
    if not text or not text.strip():
        return ("en", 0.0)

    script_result = _detect_from_script(text)
    if script_result:
        lang_code, confidence = script_result
        logger.info("Detected language by script: %s (confidence: %.2f)", lang_code, confidence)
        return (lang_code, confidence)

    try:
        from langdetect import detect_langs

        detected = detect_langs(text)
        if detected:
            top_lang = detected[0]
            mapped_code = _normalize_detected_code(top_lang.lang)
            confidence = float(top_lang.prob) if mapped_code != "en" else max(float(top_lang.prob), 0.60)
            logger.info("Detected language: %s (confidence: %.2f)", mapped_code, confidence)
            return (mapped_code, confidence)
    except ImportError:
        logger.warning("langdetect not installed. Falling back to English.")
    except Exception as exc:
        logger.error("Language detection error: %s", str(exc))

    return ("en", 0.0)


def get_language_name(lang_code: str) -> str:
    """Return display name for a language code."""
    return LANGUAGE_NAME_MAP.get(_normalize_detected_code(lang_code), "English")


def get_tts_language_code(detected_lang: str) -> str:
    """Return TTS-compatible language code constrained to supported languages."""
    return _normalize_detected_code(detected_lang)


def is_indian_language(lang_code: str) -> bool:
    """Return True for supported Indian languages."""
    return _normalize_detected_code(lang_code) in {"hi", "te", "ta", "kn"}


def simplify_response_for_language(response: str, lang_code: str) -> str:
    """Placeholder for language-specific simplification rules."""
    return response


if __name__ == "__main__":
    # Test language detection
    print("=" * 60)
    print("Language Detector Test")
    print("=" * 60)
    
    test_texts = [
        "Hello, how can I help you?",
        "नमस्ते, मैं आपकी कैसे मदद कर सकता हूं?",
        "నమస్కారం, నేను మీకు ఎలా సహాయం చేయగలను?",
        "வணக்கம், நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
        "Hola, ¿cómo puedo ayudarte?",
    ]
    
    for text in test_texts:
        lang, conf = detect_language(text)
        name = get_language_name(lang)
        print(f"\nText: {text[:50]}...")
        print(f"Language: {name} ({lang}) - Confidence: {conf:.2%}")
