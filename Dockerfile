# Production Multi-Stage Dockerfile for Panama PortOps-AI MLOps Platform
# Adheres strictly to MLOps Masterclass Section 20:
# - Minimal secure base (python:3.12-slim)
# - Non-root execution user for container security
# - Layer cache optimization
# - No hardcoded secrets

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies (build-essential, libgomp for LightGBM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create non-root application user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs /app/reports /app/models && \
    chown -R appuser:appuser /app

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser apps/ ./apps/
COPY --chown=appuser:appuser configs/ ./configs/
COPY --chown=appuser:appuser data/gold/ ./data/gold/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser reports/ ./reports/
COPY --chown=appuser:appuser mlflow.db ./mlflow.db

# Switch to non-root user
USER appuser

EXPOSE 8000 8501

# Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Run FastAPI serving microservice
CMD ["uvicorn", "src.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
