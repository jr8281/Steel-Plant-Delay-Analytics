# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /tmp
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Security: Run as non-root user
RUN groupadd -r streamapp && useradd -r -g streamapp streamapp

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/streamapp/.local
ENV PATH=/home/streamapp/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy application
COPY --chown=streamapp:streamapp frontend/ .

# Switch to non-root user
USER streamapp

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.headless=true"]