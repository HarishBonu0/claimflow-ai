# Voice Assistant Module

Voice interaction layer for Insurance Claims + Financial Literacy RAG system.

## Features

✅ **Speech-to-Text** - Convert user voice to text using Whisper  
✅ **Text-to-Speech** - Convert AI responses to voice using gTTS  
✅ **Complete Pipeline** - Voice-to-voice interaction with RAG + Gemini  
✅ **Multi-language** - Auto-detect input, support multiple output languages  
✅ **Error Handling** - Graceful fallback for all voice operations  

---

## Installation

### 1. Install Voice Dependencies

```bash
pip install -r voice/requirements.txt
```

**Core Dependencies:**
- `openai-whisper` - Speech recognition
- `gtts` - Text-to-speech
- `sounddevice` + `scipy` - Audio recording
- `playsound` - Audio playback
- `torch` + `torchaudio` - Whisper backend

### 2. Verify Installation

```bash
python voice/stt.py
python voice/tts.py
```

---

## Usage

### Option 1: Use Existing Audio File

```python
from voice.voice_pipeline import voice_chat

# Process audio file
result = voice_chat("user_question.wav")

print(result['user_text'])   # Transcribed question
print(result['ai_text'])     # AI response text
print(result['audio_file'])  # Path to voice response
```

### Option 2: Interactive Voice Chat

```python
from voice.voice_pipeline import interactive_voice_chat

# Record from microphone and get voice response
interactive_voice_chat(duration=5, language='en')
```

### Option 3: Manual Step-by-Step

```python
from voice.stt import speech_to_text, record_audio
from voice.tts import text_to_speech, play_audio
from rag.retriever import retrieve_context
from llm.gemini_client import generate_response

# Step 1: Record or load audio
audio_file = record_audio(duration=5)

# Step 2: Convert speech to text
user_text = speech_to_text(audio_file)

# Step 3: Get context from RAG
context = retrieve_context(user_text)

# Step 4: Generate AI response
ai_text = generate_response(user_text, context)

# Step 5: Convert to speech
audio_output = text_to_speech(ai_text, "response.mp3")

# Step 6: Play response
play_audio(audio_output)
```

---

## Module Details

### `voice/stt.py` - Speech-to-Text

**Functions:**

```python
speech_to_text(audio_path)
# Converts audio file to text using Whisper
# Returns: Transcribed text string

record_audio(duration=5, output_file="user_input.wav")
# Records audio from microphone
# Returns: Path to recorded audio file
```

**Features:**
- Auto-detects language
- Supports: English, Hindi, Telugu, and 90+ languages
- Works with: .wav, .mp3, .m4a, .ogg, .flac

### `voice/tts.py` - Text-to-Speech

**Functions:**

```python
text_to_speech(text, output_file="response.mp3", language='en')
# Converts text to speech audio
# Returns: Path to audio file

play_audio(audio_file)
# Plays audio file (cross-platform)
```

**Supported Languages:**
- `en` - English
- `hi` - Hindi
- `te` - Telugu
- And 50+ more languages

### `voice/voice_pipeline.py` - Complete Pipeline

**Functions:**

```python
voice_chat(audio_file, output_audio="response.mp3", language='en')
# Complete STT → RAG → Gemini → TTS pipeline
# Returns: Dictionary with user_text, ai_text, audio_file, success

interactive_voice_chat(duration=5, language='en')
# Records from mic and provides voice response
```

**Flow:**
1. Speech → Text (Whisper)
2. Retrieve Context (RAG)
3. Generate Response (Gemini)
4. Text → Speech (gTTS)

---

## Examples

### Example 1: Insurance Question

```python
from voice.voice_pipeline import voice_chat

# User asks: "What is a deductible?"
result = voice_chat("insurance_question.wav")

# Output:
# user_text: "What is a deductible?"
# ai_text: "A deductible is the money you pay first when..."
# audio_file: "response.mp3"
```

### Example 2: Financial Literacy Question

```python
from voice.voice_pipeline import voice_chat

# User asks: "How can I save money in 5 years?"
result = voice_chat("finance_question.wav", language='en')

# Gets comprehensive response from RAG + Gemini
# Returns voice answer as MP3
```

### Example 3: Multi-language Output

```python
from voice.tts import text_to_speech

# English
text_to_speech("Your claim is approved", "en_response.mp3", language='en')

# Hindi
text_to_speech("आपका दावा स्वीकृत है", "hi_response.mp3", language='hi')

# Telugu
text_to_speech("మీ దావా ఆమోదించబడింది", "te_response.mp3", language='te')
```

---

## Testing

### Test STT

```bash
python voice/stt.py
```

### Test TTS

```bash
python voice/tts.py
```

### Test Complete Pipeline

```bash
python voice/voice_pipeline.py
```

---

## Error Handling

All functions include graceful error handling:

**STT Errors:**
- Audio file not found → Returns error message
- Whisper not installed → Returns installation instruction
- Unclear audio → Returns "Could not understand" message

**TTS Errors:**
- gTTS fails → Returns None, text response still available
- No audio output → System continues with text-only response

**Pipeline Errors:**
- Any step fails → Returns partial result with error info
- Success flag indicates completion status

---

## Performance

**Whisper Model:** `base` (74M parameters)
- Speed: ~2-5 seconds for 5-second audio
- Accuracy: 95%+ for clear speech
- Languages: 90+ supported

**gTTS:**
- Speed: ~1-2 seconds per response
- Quality: Natural Google voices
- Languages: 50+ supported

**Total Pipeline:**
- Typical: 5-10 seconds end-to-end
- Includes: STT + RAG + Gemini + TTS

---

## Requirements

**Minimum:**
- Python 3.8+
- 2GB RAM (for Whisper base model)
- Microphone (for recording)
- Speakers/headphones (for playback)

**Recommended:**
- Python 3.10+
- 4GB RAM
- Good quality microphone
- Fast internet (for gTTS)

---

## Troubleshooting

### "Whisper not installed"
```bash
pip install openai-whisper
```

### "gTTS not installed"
```bash
pip install gtts
```

### "sounddevice not installed"
```bash
pip install sounddevice scipy
```

### Microphone not working
- Check system permissions
- Verify microphone is connected
- Test with other apps first

### Audio playback issues
```bash
pip install playsound
```

If still issues, audio files are saved - play manually.

---

## Architecture

```
User Voice Input
       ↓
[voice/stt.py] → Whisper → Text
       ↓
[rag/retriever.py] → ChromaDB → Context
       ↓
[llm/gemini_client.py] → Gemini → Response
       ↓
[voice/tts.py] → gTTS → Audio
       ↓
AI Voice Output
```

---

## Integration with Main System

Voice module integrates seamlessly:

```python
# Existing system (text-based)
from rag.retriever import retrieve_context
from llm.gemini_client import generate_response

query = "What is a claim?"
context = retrieve_context(query)
answer = generate_response(query, context)

# New system (voice-based)
from voice.voice_pipeline import voice_chat

result = voice_chat("user_audio.wav")
# Same RAG + Gemini pipeline
# But with voice input/output
```

No changes to existing code needed!

---

## License

Same as parent project.

## Support

For issues or questions, refer to main project documentation.
