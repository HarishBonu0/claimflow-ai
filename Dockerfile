FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG INSTALL_SYSTEM_MEDIA_DEPS=false

WORKDIR /app

# Optional OCR/voice runtime dependencies for image document verification and audio conversion.
RUN if [ "$INSTALL_SYSTEM_MEDIA_DEPS" = "true" ]; then \
            apt-get update \
            && apt-get install -y --no-install-recommends ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin \
            && rm -rf /var/lib/apt/lists/*; \
        fi

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
