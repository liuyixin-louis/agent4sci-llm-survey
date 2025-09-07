# Multi-stage build for LLM Surveying LLMs
# Stage 1: Builder
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-cli

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data /app/outputs /app/cache /app/logs

# Copy application code
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY tests/ /app/tests/
COPY *.py /app/
COPY *.md /app/
COPY requirements.txt /app/
COPY .env.example /app/

# Set environment variables (can be overridden at runtime)
ARG ANTHROPIC_API_KEY=""
ARG SCIMCP_DATA_PATH="/app/data/all_papers.parquet"
ARG CACHE_DIR="/app/cache"
ARG LOG_LEVEL="INFO"

ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV SCIMCP_DATA_PATH=${SCIMCP_DATA_PATH}
ENV CACHE_DIR=${CACHE_DIR}
ENV LOG_LEVEL=${LOG_LEVEL}
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Validate environment\n\
if [ -z "$ANTHROPIC_API_KEY" ]; then\n\
    echo "Warning: ANTHROPIC_API_KEY not set. API operations will fail."\n\
fi\n\
\n\
# Create cache directories if they dont exist\n\
mkdir -p /app/data /app/outputs /app/cache /app/logs\n\
\n\
# Check if data file exists\n\
if [ ! -f "$SCIMCP_DATA_PATH" ]; then\n\
    echo "Warning: Data file not found at $SCIMCP_DATA_PATH"\n\
    echo "Please mount your data volume or download the dataset"\n\
fi\n\
\n\
echo "LLM Surveying LLMs - Docker Container Ready"\n\
echo "======================================"\n\
echo "Python version: $(python --version)"\n\
echo "Claude CLI: $(claude --version 2>/dev/null || echo 'Not available')"\n\
echo "Working directory: $(pwd)"\n\
echo "Data path: $SCIMCP_DATA_PATH"\n\
echo "Cache directory: $CACHE_DIR"\n\
echo "======================================"\n\
\n\
# Execute command\n\
exec "$@"' > /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Define volumes
VOLUME ["/app/data", "/app/outputs", "/app/cache"]

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Expose port for FastAPI
EXPOSE 8000

# Default command - run FastAPI server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; import pandas; import numpy; sys.exit(0)" || exit 1

# Labels
LABEL maintainer="Agents4Science Team"
LABEL version="1.0.0"
LABEL description="LLM Surveying LLMs - Automated Scientific Survey Generation"
LABEL org.opencontainers.image.source="https://github.com/agents4science/llm-surveying-llms"