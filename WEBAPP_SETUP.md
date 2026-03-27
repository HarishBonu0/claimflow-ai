# ClaimFlow AI Web App Setup

This project now runs as:
- FastAPI backend (Python)
- React frontend (Vite)

## 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 2. Start backend

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

API base URL: `http://localhost:8000`

## 3. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## API Endpoints

- `GET /health`
- `POST /chat`
- `POST /voice`
- `POST /voice-input`
- `POST /upload`
- `POST /upload-document`
- `GET /history/{session_id}`

## Notes

- Supported languages: English, Telugu, Hindi, Tamil, Kannada.
- Voice recognition retries once before returning an error.
- No typing placeholder messages are shown by the frontend.
- Upload supports `.pdf`, `.jpg`, `.jpeg`, `.png`.
