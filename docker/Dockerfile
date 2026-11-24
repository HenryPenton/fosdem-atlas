# ── JS builder stage ──────────────────────────────────────────────────────────
FROM node:24-slim AS js-builder

WORKDIR /app/scripts/site

RUN npm install -g pnpm@9.15.0

COPY scripts/site/package.json scripts/site/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY scripts/site/src ./src
COPY scripts/site/tsconfig.json ./
RUN pnpm build

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.13.9-debian-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/venv \
    UV_PYTHON=3.14 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PYTHON_PREFERENCE=only-managed \
    UV_LINK_MODE=copy

# Install Python and dependencies first so this layer is cached until the lockfile changes
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# CA certificates so the scraper can fetch the schedule over HTTPS
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user; the app only writes to /app/data
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/data && \
    chown app:app /app/data

COPY src/ src/
COPY --from=js-builder /app/src/static/js/ src/static/js/

USER app

ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FOSDEM_HOST=0.0.0.0
ENV FOSDEM_PORT=8000
ENV FOSDEM_DATABASE_PATH=/app/data/fosdem.duckdb

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx2; httpx2.get('http://localhost:8000/health').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "9"]
