# Self-Hosting Guide

Run your own instance of FOSDEM Atlas with Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

## Quick Start

```bash
git clone https://github.com/HenryPenton/fosdem-atlas.git
cd fosdem-atlas
```

The app is available at <http://localhost:8000>. The FOSDEM schedule will be scraped automatically on startup and refreshed every 5 minutes.

## Docker Compose Reference

The repository ships a ready-to-use `docker-compose.yml`:

```yaml
services:
  fosdem-atlas:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - fosdem-data:/app/data
    environment:
      - FOSDEM_DEBUG=false
      - FOSDEM_SCRAPE_INTERVAL_MINUTES=5
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  fosdem-data:
```

### Using a Pre-Built Image

To skip building locally, point at the published container image:

```yaml
services:
  fosdem-atlas:
    image: ghcr.io/henrypenton/fosdem-atlas:latest
    ports:
      - "8000:8000"
    volumes:
      - fosdem-data:/app/data
    restart: unless-stopped

volumes:
  fosdem-data:
```

## Environment Variables

| Variable                         | Default              | Description                    |
| -------------------------------- | -------------------- | ------------------------------ |
| `FOSDEM_DEBUG`                   | `false`              | Enable FastAPI debug mode      |
| `FOSDEM_PORT`                    | `8000`               | Port the server listens on     |
| `FOSDEM_DATABASE_PATH`           | `data/fosdem.duckdb` | Path to the DuckDB file        |
| `FOSDEM_SCRAPE_INTERVAL_MINUTES` | `5`                  | Minutes between schedule syncs |

## Data Persistence

The DuckDB database is stored inside the `fosdem-data` Docker volume (mounted at `/app/data`). The volume survives container restarts and upgrades.

To back up the database:

```bash
docker cp $(docker-compose ps -q fosdem-atlas):/app/data/fosdem.duckdb ./fosdem-backup.duckdb
```

## Updating

```bash
cd fosdem-atlas
git pull
docker-compose up -d --build
```

Or, if using the pre-built image:

```bash
docker-compose pull
docker-compose up -d
```

## Health Check

The app exposes a `/health` endpoint that returns JSON:

```json
{"status": "healthy", "version": "2.2.0", "events": 842}
```

Docker's built-in health check calls this endpoint every 30 seconds. Monitor status with:

```bash
docker inspect --format='{{.State.Health.Status}}' $(docker-compose ps -q fosdem-atlas)
```

## Reverse Proxy

When running behind nginx, Caddy, or Traefik, proxy requests to port 8000. Example with Caddy:

```
fosdem.example.com {
    reverse_proxy fosdem-atlas:8000
}
```

## Important Notes

- **Single worker only** — DuckDB is an embedded, single-process database. Do not run multiple app workers or replicas against the same database file. Within a single worker, concurrent requests are safe: each thread gets its own DuckDB connection via `threading.local()`.
- The scraper fetches from `https://fosdem.org/2026/schedule/xml`. No API key is required.
