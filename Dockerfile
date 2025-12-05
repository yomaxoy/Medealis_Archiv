# =============================================================================
# Medealis Warehouse Management System - Docker Image
# =============================================================================
# Multi-stage build für optimale Image-Größe
# =============================================================================

FROM python:3.11-slim as base

# System-Dependencies für Pillow/OpenCV und TrueType Fonts
RUN apt-get update && apt-get install -y     libgl1     libglib2.0-0     fonts-liberation     fonts-dejavu     fontconfig     && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY config/ ./config/
COPY src/ ./src/
COPY resources/ ./resources/

# Data-Verzeichnis für Logs und Temp
RUN mkdir -p /app/data/logs /app/data/temp

# Umgebungsvariablen setzen
ENV PYTHONUNBUFFERED=1     ENVIRONMENT=production     DEBUG=False

# Ports für Streamlit Apps
EXPOSE 8501 8502

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3     CMD python -c "import requests; requests.get('http://localhost:8501')"

# Entrypoint-Script wird über docker-compose definiert
