"""
Voice Pipeline: Complete voice-to-voice interaction.
Integrates STT → RAG → Gemini → TTS.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice.stt import speech_to_text
from voice.tts import text_to_speech, play_audio


def voice_chat(audio_file, output_audio="response.mp3", language='en'):
    """
    Complete voice interaction pipeline.
    
    Flow:
    1. Convert user speech to text (STT)
    2. Retrieve context from RAG
    3. Generate response using Gemini
    4. Convert response to speech (TTS)
    
    Args:
        audio_file: Path to user's audio input
        output_audio: Path for AI response audio
        language: Language code for TTS (en, hi, te)
    
    Returns:
        Dictionary with:
        - user_text: Transcribed user question
        - ai_text: AI response text
        - audio_file: Path to AI response audio
        - success: Boolean indicating success
    """
    
    result = {
        'user_text': '',
        'ai_text': '',
        'audio_file': None,
        'success': False
    }
    
    # Step 1: Speech to Text
    print("\n[Step 1/4] Converting speech to text...")
    user_text = speech_to_text(audio_file)
    
    if user_text.startswith("Error:"):
        result['user_text'] = user_text
        result['ai_text'] = "Sorry, I could not understand your question. Please try again."
        print(f"✗ STT failed: {user_text}")
        return result
    
    result['user_text'] = user_text
    print(f"✓ User said: {user_text}")
    
    # Step 2: Retrieve context from RAG
    print("\n[Step 2/4] Retrieving context from knowledge base...")
    try:
        from rag.retriever import retrieve_context
        context = retrieve_context(user_text)
        print(f"✓ Retrieved {len(context)} characters of context")
    except Exception as e:
        result['ai_text'] = f"Error retrieving context: {str(e)[:100]}"
        print(f"✗ RAG error: {e}")
        return result
    
    # Step 3: Generate response using Gemini
    print("\n[Step 3/4] Generating AI response...")
    try:
        from llm.gemini_client import generate_response
        ai_text = generate_response(user_text, context)
        result['ai_text'] = ai_text
        print(f"✓ AI response: {ai_text[:100]}...")
    except Exception as e:
        result['ai_text'] = f"Error generating response: {str(e)[:100]}"
        print(f"✗ Gemini error: {e}")
        return result
    
    # Step 4: Text to Speech
    print("\n[Step 4/4] Converting response to speech...")
    audio_path = text_to_speech(ai_text, output_audio, language=language)
    
    if audio_path:
        result['audio_file'] = audio_path
        result['success'] = True
        print(f"✓ Voice response saved to: {audio_path}")
    else:
        print("✗ TTS failed, but text response is available")
    
    return result


def interactive_voice_chat(duration=5, language='en'):
    """
    Interactive voice chat session.
    Records from microphone and provides voice response.
    
    Args:
        duration: Recording duration in seconds
        language: Language code for TTS
    """
    
    from voice.stt import record_audio
    
    print("=" * 70)
    print("VOICE ASSISTANT - Insurance & Financial Literacy")
    print("=" * 70)
    
    # Record audio
    print(f"\n🎤 Recording for {duration} seconds...")
    audio_file = record_audio(duration=duration, output_file="user_voice.wav")
    
    if not audio_file:
        print("✗ Recording failed.")
        return
    
    # Process voice input
    result = voice_chat(audio_file, output_audio="ai_response.mp3", language=language)
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\n👤 You asked: {result['user_text']}")
    print(f"\n🤖 AI response: {result['ai_text']}")
    
    if result['success'] and result['audio_file']:
        print(f"\n🔊 Playing voice response...")
        play_audio(result['audio_file'])
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("Voice Pipeline Test")
    print("=" * 70)
    
    # Test with existing audio file
    test_audio = "sample.wav"
    
    if os.path.exists(test_audio):
        print(f"\n[Test Mode] Using existing audio: {test_audio}")
        result = voice_chat(test_audio)
        
        print("\n" + "=" * 70)
        print("Test Results")
        print("=" * 70)
        print(f"User Text: {result['user_text']}")
        print(f"AI Text: {result['ai_text']}")
        print(f"Audio File: {result['audio_file']}")
        print(f"Success: {result['success']}")
        
        if result['audio_file']:
            play_audio(result['audio_file'])
    else:
        print(f"\n[Interactive Mode] No test audio found.")
        print("Starting interactive voice chat...")
        print("You'll be asked to speak for 5 seconds.\n")
        
        response = input("Press Enter to start recording (or 'q' to quit): ")
        if response.lower() != 'q':
            interactive_voice_chat(duration=5)
