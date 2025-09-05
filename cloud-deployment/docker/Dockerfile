# MorningAI Core - Production Dockerfile
# Multi-stage build for optimization and security

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Add labels for metadata
LABEL maintainer="MorningAI Team <team@morningai.com>" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="morningai-core" \
      org.label-schema.description="MorningAI Core API with GPT+RAG integration" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/RC918/morningai-core" \
      org.label-schema.schema-version="1.0"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/morningai-api/requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r morningai && useradd -r -g morningai morningai

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY backend/morningai-api/src ./src
COPY backend/morningai-api/alembic.ini .
COPY backend/morningai-api/alembic ./alembic

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R morningai:morningai /app && \
    chmod -R 755 /app

# Switch to non-root user
USER morningai

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKERS=1 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE $PORT

# Start command with proper signal handling
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers $WORKERS --access-log --log-level info"]

