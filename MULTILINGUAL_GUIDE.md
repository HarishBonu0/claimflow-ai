# ClaimFlow AI - Multilingual & Document Support Guide

## Overview

ClaimFlow AI is now a **fully multilingual insurance assistant** with automatic language detection, voice support in 9+ languages, and intelligent document analysis. This guide explains how to use all the features.

---

## 🌍 Language Support

### Supported Languages
- 🇮🇳 **Hindi** (हिंदी)
- 🇮🇳 **Telugu** (తెలుగు)
- 🇮🇳 **Tamil** (தமிழ்)
- 🇮🇳 **Kannada** (ಕನ್ನಡ)
- 🇬🇧 **English**
- 🇪🇸 **Spanish**
- 🇫🇷 **French**
- 🇩🇪 **German**
- 🇵🇹 **Portuguese**
- 🇯🇵 **Japanese**
- 🇨🇳 **Chinese** (Simplified & Traditional)

### Automatic Language Detection

ClaimFlow AI **automatically detects** the language you use and responds in the **same language**:

#### Example 1: English Query
```
User: "What documents do I need for a health insurance claim?"
Response: [Detailed answer in English with step-by-step instructions]
```

#### Example 2: Hindi Query
```
User: "स्वास्थ्य बीमा क्लेम के लिए कौन से दस्तावेज चाहिए?"
Response: [Detailed answer in Hindi with step-by-step instructions]
```

#### Example 3: Telugu Query
```
User: "ఆరోగ్య బీమా క్లెయిమ్ కోసం ఏ డాక్యుమెంట్‌లు అవసరం?"
Response: [Detailed answer in Telugu with step-by-step instructions]
```

---

## 🎤 Voice Input & Output

### Recording Voice Input

1. **Click the microphone button** 🎙️ next to the chat input
2. **Speak in any language** (English, Hindi, Telugu, Tamil, Kannada, etc.)
3. **Click "Process"** to convert to text
4. The system will generate a text response

### Voice Response Language

1. **Select language** from the sidebar:
   - Use the **"Voice Response Language"** dropdown
   - Choose from 9+ languages
   
2. **Automatic playback**:
   - Response will be converted to speech in your selected language
   - Click **"Play"** button to hear the response

### How It Works

```
You (speak in any language)
    ↓
Whisper STT (converts speech to text)
    ↓
ClaimFlow AI (understands your language, generates response in same language)
    ↓
gTTS (converts response to speech in selected voice language)
    ↓
You hear the response
```

---

## 📄 Document Upload & Analysis

### Supported Document Types

ClaimFlow AI can analyze:

- **Insurance Policies** (PDF)
- **Claim Forms** (PDF, images)
- **Medical Bills** (PDF, images)
- **Hospital Reports** (PDF, images)
- **Accident Reports** (PDF, images)
- **Prescription Documents** (images with OCR)
- **Any document with text** (scanned or digital)

### Supported File Formats

- **PDF** - Digital documents ✅
- **Images** - JPG, PNG, BMP, TIFF ✅
- **Scanned Documents** - Automatically extracted with OCR ✅

### How to Upload Documents

1. **Click the document button** 📄 next to the chat input
2. **Choose file** from your computer:
   - Drag & drop a PDF or image
   - Or click to browse
3. **Select OCR Language** (if uploading images):
   - Hindi, English, Telugu, Tamil, Kannada, etc.
4. **Click "Process"**

### What Happens During Analysis

```
Document Upload
    ↓
Type Detection (PDF? Image?)
    ↓
Text Extraction:
  - PDF: pdfplumber (extracts text)
  - Image: Tesseract OCR (reads text from images)
    ↓
Document Analysis:
  - Detect document type (claim form, policy, bill, etc.)
  - Extract amounts and dates
  - Identify missing information
  - Verify completeness
    ↓
You can ask questions about the document
```

### Example: Uploading a Claim Form

```
1. Click 📄 document button
2. Upload your claim form (PDF or image)
3. System shows:
   - ✅ What's complete
   - ⚠️ What's missing
   - 📋 Suggested next steps

4. Ask questions:
   - "Is this filled correctly?"
   - "What's missing?"
   - "Can you explain section 3?"

5. AI responds with document-aware answers
```

---

## 🔍 Key Features

### 1. Multi-Step Responses

ClaimFlow AI formats answers as easy-to-follow steps:

```
Step 1: File a claim notification with your insurance company
Step 2: Collect all required documents
Step 3: Submit the complete claim form
Step 4: Wait for approval (usually 7-30 days)
```

### 2. Language-Specific Explanations

Responses are tailored to each language with:
- ✅ Simple vocabulary (no legal jargon)
- ✅ Short sentences (good for voice)
- ✅ Cultural context (where applicable)
- ✅ Local examples (Indian languages get Indian examples)

### 3. Document-Aware Answers

When you upload a document, the AI:
- 🔍 References specific information from your document
- 📌 Identifies issues before submission
- 🎯 Provides document-specific guidance
- ✅ Checks for completeness

### 4. Voice-Optimized

All responses are generated with voice playback in mind:
- Short sentences ✅
- Clear pronunciation ✅
- Native scripts (not romanized) ✅
- Proper punctuation for pauses ✅

---

## 💡 Usage Examples

### Example 1: English Text Query

```
User: "What documents are needed for a vehicle insurance claim?"

Response:
To file a vehicle insurance claim, gather these documents:

Step 1: Claim Form - Get from your insurance company
Step 2: Original Policy Document
Step 3: Proof of Ownership - Registration certificate
Step 4: Medical Reports - If there are injuries
Step 5: Police Report - If it's an accident
Step 6: Photos of Damage - Take clear photos
Step 7: Repair Quotations - From authorized service centers

Submit all documents to your insurance company.
```

### Example 2: Hindi Voice Query

```
User (speaks): "मेरा क्लेम रिजेक्ट हो गया, अब क्या करूं?"

Response (in Hindi):
आपका क्लेम अगर रिजेक्ट हो गया है, तो यह स्टेप्स करें:

स्टेप 1: अपनी बीमा कंपनी को कॉल करें
स्टेप 2: रिजेक्शन का कारण जानें
स्टेप 3: दोबारा अपील दाखिल करें
स्टेप 4: सभी दस्तावेज के साथ अपील करें

[Plays voice response in Hindi]
```

### Example 3: Document Analysis

```
User: [Uploads hospital bill]
"Is this bill complete for my claim?"

Response:
I've analyzed your hospital bill:

✅ Complete Information:
- Hospital name and address ✓
- Patient name ✓
- Treatment dates ✓
- Total amount ✓

⚠️ Missing Information:
- Doctor's name is unclear
- Medical condition not mentioned
- Itemized charges list is incomplete

Next Steps:
Step 1: Contact the hospital for clarification
Step 2: Get an itemized bill
Step 3: Get doctor's signature on the bill
Step 4: Submit with your claim form
```

### Example 4: Telugu With Local Language Support

```
User (speaks Telugu): "ఎలాంటి డాక్యుమెంట్‌లు క్లెం కోసం అవసరం?"

Response (in Telugu):
ఆర్థిక సహాయ కోసం ఈ డాక్యుమెంట్‌లు అవసరం:

స్టెప్ 1: క్లెం ఫారమ్‌ను పూరించండి
స్టెప్ 2: మీ పాలసీ రకం మరియు నంబర్‌ను సమర్పించండి
స్టెప్ 3: ఔషధ మరియు ఆసుపత్రి నివేదికలు ఇవ్వండి
స్టెప్ 4: చెల్లింపు రసీదులను జోడించండి

[Plays response in Telugu]
```

---

## 🛠️ Technical Implementation

### System Prompt

ClaimFlow AI uses a comprehensive system prompt that:
- Instructs the AI to detect language automatically
- Guides response formatting (Step 1, Step 2, etc.)
- Ensures document-aware answers
- Optimizes for voice playback
- Maintains cultural sensitivity

See `system_prompt.md` for full instructions.

### Language Detection

**Module:** `utils/language_detector.py`

```python
detect_language(text) → (language_code, confidence)
```

- Uses `langdetect` library
- Returns ISO language codes (en, hi, te, ta, kn, etc.)
- Provides confidence score
- Maps to gTTS language codes

### Document Processing

**Module:** `utils/document_processor.py`

```python
process_document(file_path, file_type) → {text, analysis}
```

- **PDF**: Uses `pdfplumber` for text extraction
- **Images**: Uses `pytesseract` for OCR
- **Analysis**: Detects document type, extracts amounts/dates
- **Languages**: Supports OCR in 9 languages

### Voice Handling

**Modules:** `voice/stt.py`, `voice/tts.py`

```python
speech_to_text(audio_file) → text  # Whisper with auto language detection
text_to_speech(text, language) → audio_file  # gTTS with language support
```

---

## 📋 Sidebar Features

### Language Settings
- **Voice Response Language**: Choose language for voice playback
- **Language Support Info**: View all supported languages
- **Auto-Detection**: Enabled by default

### Document Management
- **Upload Document**: Click 📄 to upload
- **View Document**: See extracted text
- **Clear Document**: Remove from session

### Chat History
- **New Chat**: Start fresh conversation
- **Previous Chats**: Access past conversations
- **Delete Chat**: Remove individual chats
- **Clear All**: Delete chat history

---

## ⚠️ Important Notes

### For Users
1. **Speak naturally** - No need to slow down speech
2. **Any language** - Mix English and Indian languages if needed
3. **Voice quality** - Speak clearly for best STT accuracy
4. **Documents** - Upload clear scans for best OCR results
5. **Patience** - First response may take 5-10 seconds

### For OCR
- Clear, scanned documents work best
- Dark text on light background is optimal
- Multiple language support available
- Handwritten text may not be fully recognized

### For Voice Responses
- Responses are optimized for text-to-speech playback
- Short, clear sentences are used
- Native scripts (not romanized) for Indian languages
- Natural pauses included

---

## 🚀 Getting Started

### First Time Users

1. **Try Text**: Ask a question in English or any supported language
2. **Upload Document**: Try uploading an insurance document
3. **Use Voice**: Click 🎙️ and speak to test voice input
4. **Select Language**: Choose your voice response language
5. **Ask Questions**: Get help with insurance claims!

### For Illiterate Users

1. **Use Voice Icon**: Tap 🎙️ to record question
2. **Hear Response**: Click play button 🔊 to listen
3. **Select Language**: Choose your language
4. **Ask Again**: Keep asking in your language
5. **Upload Documents**: Let AI analyze your documents

---

## 📞 Support

### Common Issues

**Speech not recognized?**
- Speak clearly
- Check microphone works
- Reduce background noise
- Try again

**Document text not extracted?**
- Ensure document is clear
- Try different language for OCR
- Verify file is PDF/image
- Check file size

**Language not detected?**
- Write longer queries (3+ words)
- Use proper script/spelling
- System defaults to English if uncertain

---

## 🎯 Next Steps

1. **Open the app** at `http://localhost:8504`
2. **Click Supported Languages** to see all languages
3. **Try different queries** in English and Indian languages
4. **Upload a document** to see document analysis
5. **Use voice** to test multilingual voice support

Enjoy using ClaimFlow AI! 🎉

---

**Version:** 2.0.0 - Multilingual with Document Support  
**Languages:** 11 (English + Hindi, Telugu, Tamil, Kannada + 6 International)  
**Features:** Text, Voice, Documents, Auto-Detection, Voice Response  
**Last Updated:** March 2026
