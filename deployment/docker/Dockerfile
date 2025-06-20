# QTE Production Dockerfile
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.12-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Add metadata
LABEL maintainer="QTE Development Team" \
      version="${VERSION}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      description="QTE Quantitative Trading Engine - Production Build"

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-prod.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy source code
COPY qte/ ./qte/
COPY setup.py pyproject.toml README.md ./

# Install QTE package
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.12-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r qte && useradd -r -g qte qte

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --from=builder /app/qte ./qte
COPY deployment/config/ ./config/
COPY deployment/scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups && \
    chown -R qte:qte /app

# Copy health check script
COPY deployment/scripts/healthcheck.py ./
RUN chmod +x scripts/*.sh

# Switch to non-root user
USER qte

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    QTE_ENV=production \
    QTE_LOG_LEVEL=INFO \
    QTE_CONFIG_PATH=/app/config

# Expose ports
EXPOSE 8080 8081 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python healthcheck.py

# Default command
CMD ["python", "-m", "qte.main", "--config", "/app/config/production.yaml"]

# Development stage (for debugging)
FROM production as development

USER root

# Install development tools
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython \
    jupyter

# Copy test files
COPY tests/ ./tests/

USER qte

CMD ["python", "-m", "qte.main", "--config", "/app/config/development.yaml"]
