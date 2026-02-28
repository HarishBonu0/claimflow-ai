"""
Voice Assistant Module for RAG + Gemini System.

Components:
- stt.py: Speech-to-Text using Whisper
- tts.py: Text-to-Speech using gTTS
- voice_pipeline.py: Complete voice interaction pipeline

Usage:
    from voice.voice_pipeline import voice_chat
    result = voice_chat("user_audio.wav")
"""

from voice.stt import speech_to_text, record_audio
from voice.tts import text_to_speech, play_audio
from voice.voice_pipeline import voice_chat, interactive_voice_chat

__all__ = [
    'speech_to_text',
    'record_audio',
    'text_to_speech',
    'play_audio',
    'voice_chat',
    'interactive_voice_chat'
]
