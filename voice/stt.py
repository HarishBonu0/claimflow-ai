"""
Speech-to-Text module using OpenAI Whisper.
Converts audio input to text for RAG processing with multilingual support.
"""

import os
import logging
import subprocess
import tempfile

logger = logging.getLogger(__name__)
_WHISPER_MODEL = None

# Language code mapping for Whisper (ISO 639-1 codes)
LANGUAGE_MAP = {
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
    'Chinese (Simplified)': 'zh',
    'Chinese (Traditional)': 'zh',
}


def _resolve_language_code(language):
    """Normalize language argument to ISO code expected by engines."""
    if language in LANGUAGE_MAP:
        return LANGUAGE_MAP[language]
    return language if language else 'en'


def _speech_to_text_whisper(audio_path, language='en', auto_detect=True):
    """Primary STT engine: OpenAI Whisper."""
    import whisper

    global _WHISPER_MODEL

    language_code = _resolve_language_code(language)
    if _WHISPER_MODEL is None:
        logger.info("Loading Whisper model (base)")
        _WHISPER_MODEL = whisper.load_model("base")

    model = _WHISPER_MODEL
    transcribe_lang = None if auto_detect else language_code

    logger.info(f"Transcribing audio from: {audio_path}")
    result = model.transcribe(
        audio_path,
        language=transcribe_lang,
        fp16=False
    )

    text = result.get("text", "").strip()
    detected_lang = result.get("language", "unknown")

    if not text:
        logger.warning("No speech detected in audio file")
        return "Error: Could not understand the audio. Please speak more clearly."

    logger.info(f"Whisper transcription successful (detected: {detected_lang})")
    logger.debug(f"Transcribed text: {text[:100]}...")
    return text


def _speech_to_text_google(audio_path, language='en'):
    """Fallback STT engine: Google SpeechRecognition API."""
    try:
        import speech_recognition as sr
    except ImportError:
        return "Error: SpeechRecognition not installed. Run: pip install SpeechRecognition"

    language_code = _resolve_language_code(language)
    recognizer = sr.Recognizer()
    temp_wav_path = None

    try:
        source_path = audio_path
        ext = os.path.splitext(audio_path)[1].lower()
        if ext not in {".wav", ".aiff", ".aif", ".flac"}:
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_wav_path = temp_wav.name
            temp_wav.close()
            cmd = ["ffmpeg", "-y", "-i", audio_path, temp_wav_path]
            logger.info("Converting audio for Google STT via ffmpeg: %s", " ".join(cmd))
            conversion = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if conversion.returncode != 0:
                logger.error("ffmpeg conversion failed: %s", conversion.stderr[:300])
                return "Error: Could not process audio format. Please try recording again."
            source_path = temp_wav_path

        with sr.AudioFile(source_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=language_code)
        text = (text or "").strip()
        if not text:
            return "Error: Could not understand the audio. Please speak more clearly."
        logger.info("Google SpeechRecognition transcription successful")
        return text
    except sr.UnknownValueError:
        return "Error: Could not understand the audio. Please speak more clearly."
    except Exception as exc:
        return f"Error: Could not process audio. {str(exc)[:100]}"
    finally:
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except OSError:
                pass


def speech_to_text(audio_path, language='en', auto_detect=True):
    """
    Convert speech audio to text using OpenAI Whisper.
    Supports multilingual recognition with proper language handling.
    
    Args:
        audio_path: Path to audio file (.wav, .mp3, .m4a, etc.)
        language: Language code (en, hi, te, ta, kn, etc.) or language name
                 (English, Hindi, Telugu, etc.). Default: 'en'
        auto_detect: If True, Whisper auto-detects language. Default: True
    
    Returns:
        Transcribed text string
    """
    
    # Validate audio file exists
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return "Error: Audio file not found."
    
    try:
        return _speech_to_text_whisper(audio_path, language=language, auto_detect=auto_detect)
    except ImportError:
        logger.warning("Whisper not installed; attempting Google SpeechRecognition fallback")
        return _speech_to_text_google(audio_path, language=language)
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Whisper failed: {error_msg[:120]}. Trying Google fallback...")
        fallback = _speech_to_text_google(audio_path, language=language)
        if not fallback.startswith("Error:"):
            return fallback
        logger.error(f"Speech recognition error: {error_msg}", exc_info=True)
        return fallback


def speech_to_text_with_retry(audio_path, language='en', max_retries=1):
    """
    Convert speech to text with retry logic for better reliability.
    
    Args:
        audio_path: Path to audio file
        language: Language code or name
        max_retries: Number of retry attempts (default: 1)
    
    Returns:
        Transcribed text or error message
    """
    for attempt in range(max_retries + 1):
        logger.info(f"Speech recognition attempt {attempt + 1}/{max_retries + 1}")

        # Prefer user's selected language first for multilingual accuracy, then fall back to auto-detect.
        language_code = _resolve_language_code(language)
        prefer_explicit_language = language_code not in {"", "en"}
        auto_detect = not prefer_explicit_language if attempt == 0 else prefer_explicit_language

        result = speech_to_text(audio_path, language=language, auto_detect=auto_detect)
        
        # If successful, return result
        if not result.startswith("Error:"):
            return result
        
        # If last attempt or no retries left, return error
        if attempt >= max_retries:
            logger.error(f"Speech recognition failed after {max_retries + 1} attempts")
            return result
        
        logger.warning(f"Attempt {attempt + 1} failed, retrying with different settings...")
    
    return result


def record_audio(duration=5, output_file="user_input.wav", language='en'):
    """
    Record audio from microphone with language-specific settings.
    
    Args:
        duration: Recording duration in seconds (default: 5)
        output_file: Output audio file path (default: "user_input.wav")
        language: Language for status messages (default: 'en')
    
    Returns:
        Path to recorded audio file, or None if failed
    """
    
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wavfile
        import numpy as np
        
        # Language-specific prompt messages
        prompts = {
            'en': f"Recording for {duration} seconds...\nSpeak now!",
            'hi': f"{duration} सेकंड के लिए रिकॉर्ड करना जारी है...\nअब बोलें!",
            'te': f"{duration} సెకన్ల కోసం రికార్డ్ చేస్తోంది...\nఇప్పుడు మాట్లాడండి!",
            'ta': f"{duration} நொடிகளுக்கு பதிவு செய்யப்படுகிறது...\nஇப்போது பேசுங்கள்!",
            'kn': f"{duration} ಸೆಕೆಂಡ್‌ಗಳ ಕಾಲ ರೆಕಾರ್ಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...\nಈಗ ಮಾತನಾಡಿ!",
        }
        
        prompt = prompts.get(LANGUAGE_MAP.get(language, language), prompts['en'])
        print(prompt)
        logger.info(f"Recording audio for {duration} seconds in {language}")
        
        # Record audio (44.1kHz sample rate, mono)
        sample_rate = 44100
        
        # Create microphone context with better error handling
        try:
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.int16
            )
            sd.wait()  # Wait for recording to complete
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None
        
        # Validate recording
        if recording is None or len(recording) == 0:
            logger.error("Recording is empty")
            return None
        
        # Save to WAV file
        wavfile.write(output_file, sample_rate, recording)
        
        logger.info(f"Recording saved to: {output_file}")
        print(f"Recording saved! ({len(recording)} samples)")
        return output_file
    
    except ImportError as e:
        error_msg = "sounddevice not installed. Run: pip install sounddevice scipy"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return None
    
    except Exception as e:
        logger.error(f"Recording error: {e}", exc_info=True)
        print(f"Recording error: {e}")
        return None


if __name__ == "__main__":
    # Test speech-to-text
    print("=" * 60)
    print("Speech-to-Text Test")
    print("=" * 60)
    
    # Option 1: Record audio from microphone
    print("\n[Option 1] Record from microphone")
    audio_file = record_audio(duration=5)
    
    if audio_file:
        text = speech_to_text(audio_file)
        print(f"\nTranscribed Text: {text}")
    
    # Option 2: Use existing audio file
    print("\n[Option 2] Use existing audio file")
    test_audio = "sample.wav"
    if os.path.exists(test_audio):
        text = speech_to_text(test_audio)
        print(f"Transcribed Text: {text}")
    else:
        print(f"Test audio file '{test_audio}' not found.")
