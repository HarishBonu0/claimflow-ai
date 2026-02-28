"""
Voice Assistant Demo
Quick test script for voice features.
"""

import os
import sys

def main():
    print("=" * 70)
    print("VOICE ASSISTANT DEMO")
    print("Insurance Claims + Financial Literacy")
    print("=" * 70)
    
    print("\nChoose an option:")
    print("1. Test with sample audio file")
    print("2. Record from microphone (5 seconds)")
    print("3. Test Speech-to-Text only")
    print("4. Test Text-to-Speech only")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        test_sample_audio()
    elif choice == "2":
        test_microphone()
    elif choice == "3":
        test_stt_only()
    elif choice == "4":
        test_tts_only()
    elif choice == "5":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")
        main()


def test_sample_audio():
    """Test with existing audio file."""
    print("\n" + "=" * 70)
    print("TEST: Sample Audio File")
    print("=" * 70)
    
    from voice.voice_pipeline import voice_chat
    
    audio_file = input("\nEnter audio file path (or press Enter for 'sample.wav'): ").strip()
    if not audio_file:
        audio_file = "sample.wav"
    
    if not os.path.exists(audio_file):
        print(f"\n✗ Audio file not found: {audio_file}")
        print("Please provide a valid audio file (.wav, .mp3, etc.)")
        return
    
    print(f"\nProcessing: {audio_file}")
    result = voice_chat(audio_file)
    
    display_results(result)


def test_microphone():
    """Test recording from microphone."""
    print("\n" + "=" * 70)
    print("TEST: Microphone Recording")
    print("=" * 70)
    
    from voice.voice_pipeline import interactive_voice_chat
    
    print("\nYou will record for 5 seconds.")
    print("Prepare your question about insurance or finance.")
    
    input("\nPress Enter when ready to record...")
    
    result = interactive_voice_chat(duration=5, language='en')
    
    if result:
        print("\n✓ Voice interaction complete!")


def test_stt_only():
    """Test Speech-to-Text only."""
    print("\n" + "=" * 70)
    print("TEST: Speech-to-Text Only")
    print("=" * 70)
    
    print("\n1. Use existing audio file")
    print("2. Record from microphone")
    
    choice = input("\nChoose (1-2): ").strip()
    
    if choice == "1":
        from voice.stt import speech_to_text
        
        audio_file = input("Enter audio file path: ").strip()
        if not os.path.exists(audio_file):
            print(f"✗ File not found: {audio_file}")
            return
        
        print("\nTranscribing...")
        text = speech_to_text(audio_file)
        print(f"\n✓ Transcribed Text:\n{text}")
    
    elif choice == "2":
        from voice.stt import record_audio, speech_to_text
        
        print("\nRecording for 5 seconds...")
        input("Press Enter to start...")
        
        audio_file = record_audio(duration=5)
        if audio_file:
            print("\nTranscribing...")
            text = speech_to_text(audio_file)
            print(f"\n✓ Transcribed Text:\n{text}")


def test_tts_only():
    """Test Text-to-Speech only."""
    print("\n" + "=" * 70)
    print("TEST: Text-to-Speech Only")
    print("=" * 70)
    
    from voice.tts import text_to_speech, play_audio
    
    print("\nEnter text to convert to speech:")
    text = input("> ").strip()
    
    if not text:
        print("✗ No text provided.")
        return
    
    print("\nChoose language:")
    print("1. English (en)")
    print("2. Hindi (hi)")
    print("3. Telugu (te)")
    
    lang_choice = input("Choose (1-3): ").strip()
    language = {'1': 'en', '2': 'hi', '3': 'te'}.get(lang_choice, 'en')
    
    print(f"\nConverting to speech ({language})...")
    audio_file = text_to_speech(text, "test_output.mp3", language=language)
    
    if audio_file:
        print(f"\n✓ Audio created: {audio_file}")
        play_audio(audio_file)


def display_results(result):
    """Display voice chat results."""
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print(f"\n👤 YOU ASKED:")
    print(f"{result['user_text']}")
    
    print(f"\n🤖 AI RESPONSE:")
    print(f"{result['ai_text']}")
    
    if result['success']:
        print(f"\n🔊 VOICE OUTPUT:")
        print(f"Audio saved to: {result['audio_file']}")
        
        play_choice = input("\nPlay audio? (y/n): ").strip().lower()
        if play_choice == 'y':
            from voice.tts import play_audio
            play_audio(result['audio_file'])
    else:
        print(f"\n⚠ Voice output not available (text response only)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
