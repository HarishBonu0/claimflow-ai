"""
Speech-to-Text module using OpenAI Whisper.
Converts audio input to text for RAG processing.
"""

import os


def speech_to_text(audio_path):
    """
    Convert speech audio to text using OpenAI Whisper.
    
    Args:
        audio_path: Path to audio file (.wav, .mp3, .m4a, etc.)
    
    Returns:
        Transcribed text string
    """
    
    # Validate audio file exists
    if not os.path.exists(audio_path):
        return "Error: Audio file not found."
    
    try:
        # Import Whisper (lazy import to avoid loading if not needed)
        import whisper
        
        # Load Whisper model (base is good balance of speed + accuracy)
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        
        # Transcribe audio
        print(f"Transcribing audio from: {audio_path}")
        result = model.transcribe(audio_path, language=None)  # Auto-detect language
        
        # Extract text
        text = result["text"].strip()
        
        if not text:
            return "Error: Could not understand the audio. Please speak clearly."
        
        print(f"Transcription successful: {text[:50]}...")
        return text
    
    except ImportError:
        return "Error: Whisper not installed. Run: pip install openai-whisper"
    
    except Exception as e:
        error_msg = str(e)
        print(f"Speech recognition error: {error_msg}")
        return f"Error: Could not process audio. {error_msg[:100]}"


def record_audio(duration=5, output_file="user_input.wav"):
    """
    Record audio from microphone.
    
    Args:
        duration: Recording duration in seconds
        output_file: Output audio file path
    
    Returns:
        Path to recorded audio file
    """
    
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wavfile
        import numpy as np
        
        print(f"Recording for {duration} seconds...")
        print("Speak now!")
        
        # Record audio (44.1kHz sample rate, mono)
        sample_rate = 44100
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16
        )
        sd.wait()  # Wait for recording to complete
        
        # Save to WAV file
        wavfile.write(output_file, sample_rate, recording)
        
        print(f"Recording saved to: {output_file}")
        return output_file
    
    except ImportError:
        print("Error: sounddevice not installed. Run: pip install sounddevice scipy")
        return None
    
    except Exception as e:
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
