"""
Text-to-Speech module using gTTS (Google Text-to-Speech).
Converts AI responses to voice output.
"""

import os


def text_to_speech(text, output_file="response.mp3", language='en'):
    """
    Convert text to speech using gTTS.
    
    Args:
        text: Text to convert to speech
        output_file: Output audio file path (mp3)
        language: Language code (en, hi, te, etc.)
    
    Returns:
        Path to audio file if successful, None if failed
    """
    
    # Validate text
    if not text or not text.strip():
        print("Error: No text provided for TTS.")
        return None
    
    try:
        # Import gTTS (lazy import)
        from gtts import gTTS
        
        print(f"Converting text to speech ({language})...")
        
        # Create TTS object
        tts = gTTS(text=text, lang=language, slow=False)
        
        # Save to file
        tts.save(output_file)
        
        print(f"Audio saved to: {output_file}")
        return output_file
    
    except ImportError:
        print("Error: gTTS not installed. Run: pip install gtts")
        return None
    
    except Exception as e:
        error_msg = str(e)
        print(f"Text-to-speech error: {error_msg}")
        return None


def play_audio(audio_file):
    """
    Play audio file (cross-platform).
    
    Args:
        audio_file: Path to audio file
    """
    
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        return
    
    try:
        # Try using playsound (simple and cross-platform)
        from playsound import playsound
        
        print(f"Playing audio: {audio_file}")
        playsound(audio_file)
        print("Audio playback complete.")
    
    except ImportError:
        print("Info: playsound not installed. Run: pip install playsound")
        print(f"Audio saved to: {audio_file}")
        print("You can play it manually.")
    
    except Exception as e:
        print(f"Playback error: {e}")
        print(f"Audio saved to: {audio_file}")


if __name__ == "__main__":
    # Test text-to-speech
    print("=" * 60)
    print("Text-to-Speech Test")
    print("=" * 60)
    
    # Test 1: English
    print("\n[Test 1] English TTS")
    test_text_en = "Hello! I am your insurance assistant. How can I help you today?"
    audio_file_en = text_to_speech(test_text_en, "test_en.mp3", language='en')
    
    if audio_file_en:
        print(f"✓ English audio created: {audio_file_en}")
        play_audio(audio_file_en)
    
    # Test 2: Hindi
    print("\n[Test 2] Hindi TTS")
    test_text_hi = "नमस्ते! मैं आपकी बीमा सहायक हूं।"
    audio_file_hi = text_to_speech(test_text_hi, "test_hi.mp3", language='hi')
    
    if audio_file_hi:
        print(f"✓ Hindi audio created: {audio_file_hi}")
    
    # Test 3: Telugu
    print("\n[Test 3] Telugu TTS")
    test_text_te = "నమస్కారం! నేను మీ బీమా సహాయకుడిని."
    audio_file_te = text_to_speech(test_text_te, "test_te.mp3", language='te')
    
    if audio_file_te:
        print(f"✓ Telugu audio created: {audio_file_te}")
