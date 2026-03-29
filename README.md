# ClaimFlow AI

A production-grade multilingual insurance claims assistant powered by generative AI, vector retrieval, and voice interaction.

## Overview

ClaimFlow AI is a full-stack application designed to help users understand insurance policies, file claims, and access financial literacy resources in their native language. The system supports English, Hindi, Telugu, Tamil, and Kannada with seamless voice input and output capabilities.

### Key Features

- **Multilingual Support**: English, Hindi, Telugu, Tamil, Kannada with automatic language detection
- **Voice Interface**: Speech-to-text input and text-to-speech output via gTTS and SpeechRecognition
- **Document Intelligence**: OCR-based extraction of claim forms, policies, and medical documents
- **RAG Pipeline**: Optional retrieval-augmented generation for context-grounded responses
- **Intent Routing**: Automatic classification of insurance, finance, and general queries
- **Session Management**: Persistent chat history and user authentication with PostgreSQL
- **Production Ready**: Comprehensive error handling, rate limiting, CORS protection, and Sentry monitoring

## Architecture

```
User Interface (React + Vite)
         |
         | HTTP/REST
         v
FastAPI Backend (api.py)
  |
  ├── Chat Pipeline
  │   ├── Language Detection
  │   ├── Intent Classification
  │   ├── RAG Retrieval (optional)
  │   └── Gemini Generation
  |
  ├── Voice Pipeline
  │   ├── Speech-to-Text
  │   ├── Language Detection
  │   └── Text-to-Speech
  |
  ├── Document Processing
  │   ├── PDF Text Extraction
  │   ├── Image OCR
  │   └── Field Extraction
  |
  └── Authentication & Sessions
      ├── PostgreSQL Storage
      ├── Session Tokens
      └── Rate Limiting

Vector Database (ChromaDB)
- Stores embeddings of insurance/finance knowledge
- Enables context-grounded responses via RAG
```

## Project Structure

```
claimflow-ai/
├── docs/                          # Documentation
│   ├── AUTH_FIX_SUMMARY.md       # Authentication implementation details
│   ├── DEPLOYMENT_VERIFICATION.md # Deployment verification checklist
│   └── DEPLOY_CHECKLIST.md       # Pre-deployment tasks
│
├── tests/                         # Test suite and demos
│   ├── test_app.py              # Application tests
│   ├── test_enhanced.py         # Enhanced functionality tests
│   ├── test_integration.py      # Integration tests
│   ├── test_models.py           # Model tests
│   └── demo_voice.py            # Voice interaction demo
│
├── backend/
│   ├── api.py                   # FastAPI application and routes
│   └── __init__.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── api.js               # API client
│   │   ├── main.jsx             # Entry point
│   │   └── styles.css           # Stylesheet
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
│
├── llm/
│   ├── gemini_client.py         # Gemini API integration
│   ├── intent_classifier.py     # Query classification
│   ├── finance_assistant.py     # Finance-specific logic
│   ├── safety_filter.py         # Content safety checks
│   ├── integration_example.py   # RAG + Gemini pipeline
│   ├── savings_engine.py        # Financial calculations
│   └── __init__.py
│
├── rag/
│   ├── build_vector_db.py       # Vector database creation
│   ├── retriever.py             # Context retrieval
│   └── __init__.py
│
├── utils/
│   ├── chat_handler.py
│   ├── document_processor.py    # PDF/image processing
│   ├── language_detector.py     # Language detection
│   └── __init__.py
│
├── voice/
│   ├── stt.py                   # Speech-to-text
│   ├── tts.py                   # Text-to-speech
│   ├── voice_pipeline.py        # Voice orchestration
│   ├── requirements.txt
│   └── __init__.py
│
├── knowledge_base/
│   ├── insurance.txt            # Insurance process knowledge
│   ├── finance.txt              # Financial concepts
│   └── __init__.py
│
├── vector_db/                   # ChromaDB embeddings storage
│   ├── chroma.sqlite3
│   └── ...
│
├── scripts/
│   ├── smoke-test-deploy.ps1    # Deployment verification script
│   └── ...
│
├── api.py                        # Production entry point
├── main.py                       # Alternative entry point
├── system_prompt.md             # System instructions for AI
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── render.yaml                  # Render deployment config
├── .env.example                 # Environment template
├── .gitignore
├── .dockerignore
└── README.md
```

## Prerequisites

- Python 3.10 or higher
- Node.js 16+ (for frontend)
- PostgreSQL database (Neon for cloud)
- Gemini API key (free at https://aistudio.google.com/apikey)
- Optional: Tesseract OCR binary for image processing

## Installation

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/claimflow-ai.git
cd claimflow-ai
```

2. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from template:
```bash
cp .env.example .env
```

5. Configure environment variables in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://user:password@host:port/dbname
APP_ENV=development
ENABLE_RAG=true
```

6. Initialize the database:
```bash
python -c "from backend.api import init_db_pool, init_db_schema; init_db_pool(); init_db_schema()"
```

7. Build the vector database (optional, for RAG):
```bash
python rag/build_vector_db.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run build
# For development:
npm run dev
```

## Running Locally

### Backend Server

```bash
python api.py
```

The FastAPI server will start at `http://localhost:8000`. Health check endpoint: `http://localhost:8000/health`

### Frontend Development

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Test Suite

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_integration.py -v

# Interactive demo
python tests/demo_voice.py
```

## API Endpoints

### Chat

`POST /chat`
- Send text message
- Parameters: `message`, `session_id`, `language`, `session_token`
- Returns: Response text, session ID, language, optional audio

### Voice

`POST /voice` or `POST /voice-input`
- Send audio file for processing
- Parameters: `audio` (file), `session_id`, `preferred_language`
- Returns: Transcribed text, generated response, audio output

### Document Upload

`POST /upload` or `POST /upload-document`
- Upload claim document (PDF or image)
- Parameters: `file` (PDF/JPG/PNG), `session_id`
- Returns: Text extraction, field analysis, verification score

### Authentication

- `POST /auth/signup` - Register new user
- `POST /auth/login` - User login
- `POST /auth/logout` - Logout
- `GET /auth/verify` - Verify session token

### Session Management

- `GET /sessions` - List user chat sessions
- `DELETE /sessions/{session_id}` - Delete a session
- `GET /history/{session_id}` - Retrieve chat history

### Health Check

`GET /health`
- System status and environment information
- Returns: Status, environment, vector backend, warnings

## Configuration

### Environment Variables

Key configuration variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection string |
| `GEMINI_API_KEY` | Required | Google Gemini API key |
| `APP_ENV` | development | Environment: development, production |
| `ENABLE_RAG` | true | Enable/disable vector retrieval |
| `AUTH_HASH_SCHEME` | bcrypt | Password hashing: bcrypt, argon2 |
| `AUTH_SESSION_HOURS` | 168 | Session token validity (hours) |
| `RATE_LIMIT_CHAT_PER_MIN` | 60 | Chat requests per minute |
| `RATE_LIMIT_VOICE_PER_MIN` | 20 | Voice requests per minute |
| `ALLOWED_ORIGINS` | localhost | CORS allowed origins |
| `SENTRY_DSN` | Optional | Sentry error tracking |

### Language Configuration

Supported languages are defined in `backend/api.py`:

```python
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
}
```

For adding new languages:
1. Update `SUPPORTED_LANGUAGES` mapping
2. Add OCR language code in `OCR_LANG_BY_CODE`
3. Add TTS voice configurations
4. Update system prompts for language-specific instructions

## Deployment

### Deploy to Render (Backend)

1. Push code to GitHub
2. In Render dashboard: New > Blueprint
3. Select repository with `render.yaml`
4. Configure environment variables:
   - `DATABASE_URL`: Neon PostgreSQL URI
   - `GEMINI_API_KEY`: Your API key
   - `ALLOWED_ORIGINS`: Frontend URL
5. Deploy via Render Blueprint

The health endpoint will be: `https://your-service.onrender.com/health`

### Deploy to Vercel (Frontend)

1. Connect GitHub repository to Vercel
2. Set root directory to `frontend/`
3. Configure build settings:
   - Build command: `npm run build`
   - Output directory: `dist`
4. Add environment variable:
   - `VITE_API_BASE_URL`: Your Render backend URL
5. Deploy

## Security Considerations

- Credentials are never logged; password hashing uses bcrypt or Argon2
- Session tokens are validated server-side before use
- Rate limiting protects against abuse
- CORS policy restricts access to whitelisted origins
- Passwords undergo sanitization to remove hidden Unicode characters
- Minimum password length: 6 characters; maximum: 1024 characters
- All inputs are validated using Pydantic models
- SQL injection prevented via parameterized queries

### Production Security Checklist

- Enable HTTPS/SSL on all endpoints
- Use environment variables for all secrets
- Set `APP_ENV=production`
- Configure Sentry for error monitoring
- Enable database backups
- Use strong PostgreSQL passwords
- Rotate API keys regularly
- Monitor rate limit thresholds
- Enable CORS only for trusted origins

## Troubleshooting

### API Connection Failed

```
Could not connect to server. Please ensure backend is running and reachable.
```

Check:
- Backend server is running on correct port
- `VITE_API_BASE_URL` points to correct host
- CORS origins are configured correctly
- Firewall allows outbound connections

### Database Connection Error

```
DATABASE_URL is required. Add Neon PostgreSQL URL to .env
```

Solution:
- Create PostgreSQL database at https://neon.tech
- Copy connection string to `.env`
- Ensure connection string includes SSL mode: `?sslmode=require`

### Gemini API Error

Verify:
- API key is valid at https://aistudio.google.com/apikey
- `GEMINI_API_KEY` is set in environment
- API quota is not exceeded
- Network allows outbound Google API requests

### Language Detection Issues

If language is misdetected:
- Check input contains native script characters
- Verify system_prompt.md has correct language instructions
- Test with pure script input (not transliterated)

### OCR Not Working

Ensure Tesseract OCR is installed:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-tel`
- **macOS**: `brew install tesseract`
- **Windows**: Download installer from https://github.com/UB-Mannheim/tesseract/wiki

## Performance Optimization

### Vector Database

For faster retrieval, build vector database at startup:

```python
# In backend/api.py
from rag.build_vector_db import build_vector_db
build_vector_db()
```

### Caching

Implement response caching for common queries:

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def cached_response(query):
    # expensive operation
    pass
```

### Connection Pooling

Database connections are pooled using psycopg2:

```python
db_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
```

Adjust `minconn` and `maxconn` based on expected load.

## Monitoring

### Health Checks

Regular health monitoring endpoint:

```bash
curl https://your-api.onrender.com/health
```

Response includes:
- System status (ok)
- Environment (production/development)
- Vector backend being used
- Warnings (e.g., missing Tesseract)

### Sentry Integration

Enable error tracking:

```python
import sentry_sdk
sentry_sdk.init(dsn="your_sentry_dsn")
```

Configure in `.env`:
```
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Logging

Logs are output to stdout for cloud environments:

```bash
# View logs in development
tail -f logs.txt

# In production (Render)
# Use Render's logs dashboard
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature: description"`
5. Push to branch: `git push origin feature/your-feature`
6. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Use type hints in function signatures
- Add docstrings to all functions
- Write tests for new features
- Keep components modular and testable

## Documentation

Additional documentation is available in the `docs/` directory:

- [AUTH_FIX_SUMMARY.md](docs/AUTH_FIX_SUMMARY.md) - Authentication implementation details
- [DEPLOYMENT_VERIFICATION.md](docs/DEPLOYMENT_VERIFICATION.md) - Production deployment checklist
- [DEPLOY_CHECKLIST.md](docs/DEPLOY_CHECKLIST.md) - Pre-deployment verification steps

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions:

1. Check existing GitHub issues
2. Review documentation in `docs/` directory
3. Open a new GitHub issue with detailed description
4. Contact the development team

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115+
- **Server**: Uvicorn
- **Database**: PostgreSQL (Neon)
- **AI/ML**: Google Gemini API, ChromaDB
- **Authentication**: Passlib, Bcrypt, Argon2
- **Voice**: SpeechRecognition, gTTS, Tesseract OCR
- **Monitoring**: Sentry SDK

### Frontend
- **Framework**: React 18.3+
- **Build Tool**: Vite 5.4+
- **UI Components**: Lucide React
- **Language**: JavaScript ES6+

### Deployment
- **Backend**: Render
- **Frontend**: Vercel
- **Database**: Neon PostgreSQL
- **Containers**: Docker
- **Vector DB**: ChromaDB

## Roadmap

Planned features and improvements:

- Multi-turn conversation context optimization
- Fine-tuned models for domain-specific responses
- Advanced document classification
- Integration with insurance provider APIs
- Advanced analytics dashboard
- Mobile app (React Native)
- Webhook support for CRM integration

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Latest Update**: March 2026  
**Version**: 1.0.0  
**Status**: Production Ready


