# Voice Assistant Setup Guide

Quick setup guide for voice features.

## Installation Steps

### Step 1: Install Voice Dependencies

```bash
pip install openai-whisper gtts sounddevice scipy playsound torch torchaudio
```

Or use the requirements file:

```bash
pip install -r voice/requirements.txt
```

### Step 2: Verify Installation

Test STT (Speech-to-Text):
```bash
python voice/stt.py
```

Test TTS (Text-to-Speech):
```bash
python voice/tts.py
```

### Step 3: Run Demo

```bash
python demo_voice.py
```

---

## Quick Start

### Option 1: Interactive Voice Chat

```python
from voice.voice_pipeline import interactive_voice_chat

# Record from microphone and get AI voice response
interactive_voice_chat(duration=5)
```

### Option 2: Process Audio File

```python
from voice.voice_pipeline import voice_chat

result = voice_chat("my_question.wav")
print(result['user_text'])
print(result['ai_text'])
```

---

## Common Issues

### Issue: "Whisper not installed"
**Solution:**
```bash
pip install openai-whisper
```

### Issue: "Module 'torch' not found"
**Solution:**
```bash
pip install torch torchaudio
```

### Issue: "sounddevice not found"
**Solution:**
```bash
pip install sounddevice scipy
```

### Issue: Microphone not working
**Solution:**
- Check system permissions
- Verify microphone is connected and working
- Try: `python -m sounddevice` to test

### Issue: Audio playback not working
**Solution:**
- Audio files are still saved even if playback fails
- Play manually or install: `pip install playsound`

---

## System Requirements

- Python 3.8+
- 2-4 GB RAM
- Microphone (for voice input)
- Internet connection (for gTTS)

---

## Testing

Run the demo script:
```bash
python demo_voice.py
```

Choose from menu:
1. Test with sample audio file
2. Record from microphone
3. Test STT only
4. Test TTS only

---

## Examples

### Example Questions (Voice Input):

**Insurance:**
- "What is a deductible?"
- "How do I file a claim?"
- "Why was my claim denied?"
- "What is the claim process?"

**Finance:**
- "What is compound interest?"
- "How can I save money?"
- "What are government savings schemes?"
- "Explain inflation in simple terms"

---

## Architecture

```
User speaks → Whisper (STT) → RAG Retrieval → Gemini AI → gTTS (TTS) → Audio plays
```

All integrated with existing RAG + Gemini system!

---

## Need Help?

See full documentation: `voice/README.md`
