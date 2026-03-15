# FOSDEM Explorer

A DuckDB-powered web application for exploring, searching, and analyzing the FOSDEM 2026 schedule.

## Features

- 🔍 **Search & Filter** - Find talks by keyword, track, speaker, or room
- 📊 **Analytics Dashboard** - Statistics and visualizations about the conference
- ⏰ **Auto-Refresh** - Schedule data scraped every 5 minutes
- 🦆 **DuckDB** - Fast analytical queries on schedule data
- 🚀 **HTMX** - Lightweight, dynamic UI without complex JavaScript

## Quick Start

### Using Docker (Recommended)

```bash
docker-compose up -d
open http://localhost:8000
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/HenryPenton/fosdem-explorer.git
cd fosdem-explorer

# Install dev dependencies (creates venv automatically)
make dev

# Run the application
make run

# Open in browser
open http://localhost:8000
```

## Development

### Prerequisites

- Python 3.13 (or edit `PYTHON` in Makefile for your version)
- Make

### Commands

```bash
make help        # Show all commands
make dev         # Create venv + install dev dependencies
make install     # Create venv + install production dependencies only
make run         # Run with auto-reload
make run-prod    # Run in production mode
make test        # Run tests
make lint        # Run linting + type checking
make format      # Format code
make clean       # Remove venv and caches
make docker-build  # Build Docker image
make docker-run    # Run Docker container
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| Frontend | HTMX, Jinja2 |
| Database | DuckDB |
| Scheduling | APScheduler |
| Containerization | Docker |

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `FOSDEM_DEBUG` | `false` | Enable debug mode |
| `FOSDEM_PORT` | `8000` | Server port |
| `FOSDEM_DATABASE_PATH` | `data/fosdem.duckdb` | DuckDB file path |
| `FOSDEM_SCRAPE_INTERVAL_MINUTES` | `5` | Scraping interval |

## Project Structure

```
fosdem-explorer/
├── src/                  # Application code
│   ├── api/             # API routes
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS assets
├── scraper/             # FOSDEM schedule scraper
├── db/                  # DuckDB schemas and migrations
├── docker/              # Docker configuration
├── tests/               # Test suite
└── data/                # DuckDB database files (gitignored)
```

## License

This project uses a dual-license approach:

| Component | License |
|-----------|---------|
| Application code | [MIT License](LICENSE) |
| FOSDEM schedule data | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

Schedule data © [FOSDEM](https://fosdem.org). See [DATA_LICENSE.md](DATA_LICENSE.md) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

- [FOSDEM](https://fosdem.org) for the amazing conference and open data
- [DuckDB](https://duckdb.org) for the embedded analytical database
- [HTMX](https://htmx.org) for simplifying dynamic web UIs
