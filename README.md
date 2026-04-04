# FOSDEM Atlas

A DuckDB-powered web application for exploring, searching, and analyzing the FOSDEM 2026 schedule.

<!-- TODO: Add screenshot of the homepage here -->

## Features

- 🔍 **Full-Text Search** — find talks by keyword across titles and abstracts
- 🎛️ **Filter by Track, Room & Day** — narrow results with live-updating dropdowns
- 📅 **Schedule Grid** — visual room × time-slot grid for each conference day
- 🎤 **Speaker & Track Browsers** — browse all speakers and tracks at a glance
- 📊 **Analytics Dashboard** — charts and stats powered by DuckDB (room heatmaps, topic trends, word clouds)
- ⭐ **Personal Schedule** — bookmark talks, detect conflicts, export to iCal
- 🌙 **Dark Mode** — automatic or manual toggle
- ⏰ **Auto-Refresh** — schedule data scraped and updated every 5 minutes
- 🦆 **DuckDB** — fast, embedded analytical queries with zero external database setup
- 🚀 **HTMX + Jinja2** — lightweight, dynamic UI without heavy JavaScript frameworks

<!-- TODO: Add screenshot of the search/filter UI here -->

## Quick Start

### Using Docker (recommended)

```bash
git clone https://github.com/HenryPenton/fosdem-atlas.git
cd fosdem-atlas
docker-compose up -d
```

Open <http://localhost:8000>. The schedule will be fetched automatically on first launch.

### Local Development

```bash
# Clone the repository
git clone https://github.com/HenryPenton/fosdem-atlas.git
cd fosdem-atlas

# Install dev dependencies (creates venv automatically)
make dev

# Run the application (auto-reload on :8000)
make run
```

Open <http://localhost:8000>.

## Self-Hosting

See the [Self-Hosting Guide](SELF_HOSTING.md) for detailed deployment instructions including Docker Compose configuration, environment variables, volume management, and production tips.

### Minimal Docker Compose

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

```bash
docker-compose up -d
```

## Screenshots

<!-- TODO: Add screenshot of the schedule grid view here -->

<!-- TODO: Add screenshot of the analytics dashboard here -->

<!-- TODO: Add screenshot of the speaker browser here -->

<!-- TODO: Add screenshot of the personal schedule / My Schedule page here -->

<!-- TODO: Add screenshot of dark mode here -->

## Development

### Prerequisites

- Python 3.13+ (edit `PYTHON` in the Makefile if your binary is named differently)
- Make

### Commands

```bash
make help          # Show all available commands
make dev           # Create venv + install dev dependencies + pre-commit hooks + build JS
make install       # Create venv + install production dependencies only
make run           # Run with auto-reload on :8000
make run-prod      # Run in production mode on :8000
make test          # Run tests
make lint          # Run ruff + mypy
make format        # Auto-format with ruff
make clean         # Remove venv and caches
make docker-build  # Build Docker image
make docker-run    # Run Docker container
make commit        # Interactive conventional commit
make bump          # Bump version + update CHANGELOG
make audit         # Check dependencies for known vulnerabilities (pip-audit)
make sbom          # Generate CycloneDX SBOM → docs/sbom.json
make build-js      # Compile TypeScript sources → src/static/js/
make test-js       # Run vitest test suite
make fake          # Generate fake schedule XML for testing
```

## Architecture

The project follows a **ports-and-adapters (hexagonal)** architecture:

```
src/
├── domain/              # Pure domain models and port interfaces (no I/O)
│   ├── models/          # Dataclasses: events, speakers, analytics, views
│   └── ports.py         # Abstract repository interfaces
├── application/         # Use-case services (depend only on domain ports)
├── adapters/
│   ├── persistence/     # DuckDB repository implementations
│   ├── scraper/         # FOSDEM XML schedule scraper
│   └── web/             # FastAPI app, routes, middleware
├── api/                 # API DTOs and routers
├── config.py            # Pydantic settings
└── main.py              # Application entry point
templates/               # Jinja2 HTML templates
static/                  # CSS and JS assets
scripts/
└── site/                # TypeScript sources compiled to static/js/
tests/                   # pytest test suite
```

## Tech Stack

| Component        | Technology              |
| ---------------- | ----------------------- |
| **Backend**      | Python + FastAPI        |
| **Database**     | DuckDB (embedded)       |
| **Scraper**      | httpx + lxml            |
| **Scheduler**    | APScheduler             |
| **Frontend**     | HTMX + Jinja2           |
| **Styling**      | Vanilla CSS             |
| **Containers**   | Docker + Docker Compose |
| **CI/CD**        | GitHub Actions          |

## Configuration

Environment variables (can be set in a `.env` file or passed to Docker):

| Variable                         | Default              | Description          |
| -------------------------------- | -------------------- | -------------------- |
| `FOSDEM_DEBUG`                   | `false`              | Enable debug mode    |
| `FOSDEM_PORT`                    | `8000`               | Server port          |
| `FOSDEM_DATABASE_PATH`           | `data/fosdem.duckdb` | DuckDB file path     |
| `FOSDEM_SCRAPE_INTERVAL_MINUTES` | `5`                  | Scraping interval    |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on setting up a dev environment, code standards, commit conventions, and the pull request process.

## License

This project uses a **dual-license** approach:

| Component            | License                                                        |
| -------------------- | -------------------------------------------------------------- |
| Application code     | [MIT](LICENSE)                                                 |
| FOSDEM schedule data | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)     |

Schedule data © [FOSDEM](https://fosdem.org). See [DATA_LICENSE.md](DATA_LICENSE.md) for details.

## Acknowledgments

- [FOSDEM](https://fosdem.org) for the amazing conference and open data
- [DuckDB](https://duckdb.org) for the embedded analytical database
- [HTMX](https://htmx.org) for simplifying dynamic web UIs
