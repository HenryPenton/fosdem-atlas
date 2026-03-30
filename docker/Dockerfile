# ── JS builder stage ──────────────────────────────────────────────────────────
FROM node:22-slim AS js-builder

WORKDIR /app/scripts/site

RUN npm install -g pnpm@9.15.0

COPY scripts/site/package.json scripts/site/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY scripts/site/src ./src
COPY scripts/site/tsconfig.json ./
RUN pnpm build

# ── Python builder stage ──────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY pyproject.toml .
RUN pip install --upgrade pip && pip install --no-cache-dir .

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/data && \
    chown -R app:app /app

# Copy venv and source from builder — no build tools in the final image
COPY --from=builder /app/venv /app/venv
COPY src/ src/
COPY --from=js-builder /app/src/static/js/ src/static/js/

RUN chown -R app:app /app
USER app

ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FOSDEM_HOST=0.0.0.0
ENV FOSDEM_PORT=8000
ENV FOSDEM_DATABASE_PATH=/app/data/fosdem.duckdb

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "9"]
