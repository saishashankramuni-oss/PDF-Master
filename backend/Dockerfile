FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PDF_MASTER_TEMP_DIR=/tmp/pdf-master

WORKDIR /app

# Install the system tools used by OCR and Office document conversions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p /tmp/pdf-master/uploads /tmp/pdf-master/outputs /tmp/pdf-master/jobs

EXPOSE 8000

# Keep the container's own health check aligned with the runtime-assigned port.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-8000}/health" || exit 1'

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
