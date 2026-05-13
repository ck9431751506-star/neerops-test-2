# NEEROps v9.0 - Dockerfile
# Multi-stage build with distroless base (production-ready)

FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt


# Production stage - distroless
FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 neerops && \
    chown -R neerops:neerops /app

USER neerops

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from config import Config; import sys; sys.exit(0 if Config.validate() else 1)"

# Entrypoint
ENTRYPOINT ["python", "cli.py"]
CMD ["start"]
