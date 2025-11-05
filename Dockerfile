# Build Nexus full-stack app for Cloud Run deployment

# Stage 1: build the Vite frontend
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build -- --logLevel warn --mode production

# Stage 2: install Python dependencies
FROM python:3.11-slim AS python-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Stage 3: runtime image
FROM python-base AS runtime

WORKDIR /app

COPY backend ./backend
COPY plugins ./plugins
COPY apps /workspace/apps
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Create non-root user and writable workdir
RUN useradd --create-home --shell /bin/sh appuser \
    && mkdir -p /workspace \
    && chown -R appuser:appuser /app /workspace
USER appuser

ENV PORT=8080 \
    NEXUS_ALLOWED_ROOT=/workspace \
    NEXUS_TASK_MODE=inline \
    PYTHONPATH=/app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\",\"8080\")}/health',timeout=3)" \
    || exit 1

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
