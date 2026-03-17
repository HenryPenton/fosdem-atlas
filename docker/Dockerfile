FROM python:3.12-slim

WORKDIR /app

# Create non-root user and venv directory
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/data && \
    chown -R app:app /app

# Create venv and install dependencies
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY pyproject.toml .
COPY src/ src/
RUN pip install --upgrade pip && pip install --no-cache-dir .

# Set ownership and switch to non-root user
RUN chown -R app:app /app
USER app

# Environment variables
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FOSDEM_HOST=0.0.0.0
ENV FOSDEM_PORT=8000
ENV FOSDEM_DATABASE_PATH=/app/data/fosdem.duckdb

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "9"]
