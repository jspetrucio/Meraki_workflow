# docker/Dockerfile
# Multi-stage build for CNL (Cisco Network Language)
# Combines frontend build + Python runtime

# Stage 1: Build frontend (when available)
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts 2>/dev/null || true
COPY frontend/ ./
RUN npm run build 2>/dev/null || mkdir -p dist

# Stage 2: Python runtime
FROM python:3.11-slim AS runtime
WORKDIR /app

# Create non-root user
RUN groupadd -r cnl && useradd -r -g cnl -d /home/cnl -m cnl

# Install system deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cache layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/
COPY templates/ ./templates/
COPY .claude/agents/ ./.claude/agents/
COPY pyproject.toml ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directories (will be overridden by volume mounts)
RUN mkdir -p /home/cnl/.cnl /home/cnl/.meraki && \
    chown -R cnl:cnl /home/cnl /app

# Switch to non-root user
USER cnl

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:3141/api/v1/health || exit 1

EXPOSE 3141

ENV CNL_HOST=0.0.0.0 CNL_PORT=3141

CMD ["python", "-m", "uvicorn", "scripts.server:app", \
     "--host", "0.0.0.0", "--port", "3141"]
