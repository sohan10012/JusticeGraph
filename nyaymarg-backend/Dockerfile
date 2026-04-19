FROM python:3.12-slim

# Security: non-root user
RUN addgroup --system nyaymarg && adduser --system --group nyaymarg

WORKDIR /app

# System build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create directories and set ownership
RUN mkdir -p app/ml/artefacts uploads data/ddl_judicial && \
    chown -R nyaymarg:nyaymarg /app

USER nyaymarg

# Prevent Matplotlib warning about writable config directory
ENV MPLCONFIGDIR=/tmp/matplotlib

# Render sets $PORT dynamically; default 8000 for local/Docker
ENV PORT=8000

EXPOSE $PORT

# 1 worker on Render free tier (512 MB RAM); scale via workers env var
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers ${WORKERS:-1}
