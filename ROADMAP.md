# FOSDEM Explorer Roadmap

A DuckDB-powered web application for exploring, searching, and analyzing the FOSDEM 2026 schedule.

## 🎯 Project Vision

Build an open-source tool that scrapes the FOSDEM schedule, stores it in DuckDB for fast analytics, and provides an intuitive interface for attendees to discover talks and gain insights into conference trends.

---

## Phase 1: Foundation & Data Layer

**Goal:** Establish the core data pipeline and storage.

### 1.1 Project Setup
- [ ] Initialize repository structure
  - `src/` - Application code
  - `scraper/` - Schedule scraping logic
  - `db/` - DuckDB schemas and queries
  - `web/` - Frontend application
  - `docker/` - Container configurations
- [ ] Choose tech stack:
  - **Backend:** Python (FastAPI) or Node.js (Express)
  - **Database:** DuckDB (embedded)
  - **Frontend:** React/Vue/Svelte (or simple HTMX for lightweight approach)
- [ ] Set up development environment (devcontainer, Makefile, scripts)
- [ ] Configure linting, formatting, and pre-commit hooks

### 1.2 Licensing & Legal Compliance
- [ ] Add `LICENSE` file with MIT license for application code
- [ ] Create `DATA_LICENSE.md` documenting FOSDEM data provenance
- [ ] Add SPDX identifiers to `package.json` / `pyproject.toml`
- [ ] Document dual-license approach in README:
  - Application code: MIT License
  - FOSDEM schedule data: CC BY 4.0
- [ ] Note in documentation that talk abstracts/bios are speaker-owned

### 1.3 FOSDEM Schedule Scraper
- [ ] Research FOSDEM data sources:
  - Primary: https://fosdem.org/2026/schedule/xml
  - Backup: HTML scraping of schedule pages
- [ ] Implement XML/HTML parser for schedule data
- [ ] Extract entities:
  - **Events:** title, abstract, start/end time, track, room, links
  - **Speakers:** name, bio, events
  - **Rooms:** name, capacity, building
  - **Tracks:** name, description
- [ ] Handle incremental updates (detect changes)
- [ ] Add error handling and retry logic
- [ ] Logging and monitoring for scrape jobs

### 1.4 DuckDB Integration
- [ ] Design database schema:
  ```sql
  -- Core tables
  events (id, title, subtitle, abstract, start_time, end_time, room_id, track_id)
  speakers (id, name, bio)
  event_speakers (event_id, speaker_id)
  rooms (id, name, building, capacity)
  tracks (id, name, description)
  
  -- Metadata
  scrape_history (id, timestamp, events_added, events_updated, status)
  ```
- [ ] Create migration system for schema changes
- [ ] Implement data access layer (DAL)
- [ ] Set up DuckDB persistence and backup strategy

### 1.5 Scheduled Scraping
- [ ] Implement scheduler (APScheduler/cron/background worker)
- [ ] Configure 5-minute scrape interval
- [ ] Add health check endpoint for scraper status
- [ ] Implement change detection to minimize database writes

---

## Phase 2: API & Core Features

**Goal:** Build the backend API and core search functionality.

### 2.1 REST API
- [ ] `/api/events` - List all events (with pagination)
- [ ] `/api/events/{id}` - Get event details
- [ ] `/api/events/search` - Search events by keyword
- [ ] `/api/speakers` - List speakers
- [ ] `/api/speakers/{id}` - Speaker details with their events
- [ ] `/api/rooms` - List rooms
- [ ] `/api/tracks` - List tracks
- [ ] `/api/schedule` - Full schedule grouped by day/time
- [ ] `/api/health` - Health check endpoint

### 2.2 Search & Discovery
- [ ] Full-text search across event titles and abstracts
- [ ] Filter by:
  - Track/topic
  - Room
  - Day/time slot
  - Speaker
- [ ] Tag extraction from event titles/abstracts (keywords, technologies)
- [ ] "Similar events" recommendations
- [ ] Personal schedule builder (save favorites)

### 2.3 Real-time Updates
- [ ] WebSocket or SSE for live schedule changes
- [ ] Notify users when watched events change
- [ ] Show "last updated" timestamp

---

## Phase 3: Frontend & Viewer

**Goal:** Create an intuitive user interface.

### 3.1 Schedule Viewer
- [ ] **Timeline view:** Visual schedule grid by room and time
- [ ] **List view:** Searchable/filterable event list
- [ ] **Calendar view:** Day-by-day calendar layout
- [ ] **Now & Next:** What's happening right now + upcoming
- [ ] Mobile-responsive design

### 3.2 Event Details
- [ ] Event page with full abstract
- [ ] Speaker information and links
- [ ] Room information with building/location
- [ ] Related events (same track, same speaker)
- [ ] Links to video recordings (post-conference)

### 3.3 Search & Filter UI
- [ ] Search bar with autocomplete
- [ ] Tag cloud for popular topics
- [ ] Filter sidebar (tracks, rooms, days)
- [ ] Saved searches / bookmarks (localStorage or account-based)

### 3.4 Personal Schedule
- [ ] Add/remove events to personal schedule
- [ ] Export to iCal (.ics file)
- [ ] Share schedule link
- [ ] Conflict detection (overlapping events)

### 3.5 Attribution UI
- [ ] Add footer attribution: "Schedule data © FOSDEM, licensed under CC BY 4.0"
- [ ] Include link to https://creativecommons.org/licenses/by/4.0/ in footer
- [ ] Display "Data sourced from fosdem.org" prominently
- [ ] Link back to original FOSDEM event pages from event details

---

## Phase 4: Analytics Dashboard

**Goal:** Leverage DuckDB for insightful statistics.

### 4.1 Conference Statistics
- [ ] Total events, speakers, tracks, rooms
- [ ] Events per track (bar chart)
- [ ] Events per room (utilization)
- [ ] Events by day and hour (heatmap)
- [ ] Average/median event duration

### 4.2 Speaker Analytics
- [ ] Top speakers by number of talks
- [ ] Speakers with multiple tracks
- [ ] New vs. returning speakers (if historical data available)
- [ ] Speaker collaboration network (co-presentations)

### 4.3 Room Analytics
- [ ] Room utilization over time
- [ ] Most/least used rooms
- [ ] Room capacity vs. actual usage (if attendance data exists)
- [ ] Building-level statistics

### 4.4 Topic/Track Trends
- [ ] Most popular tracks
- [ ] Topic word cloud from abstracts
- [ ] Technology mentions frequency
- [ ] Track clustering by content similarity

### 4.5 Interactive Queries
- [ ] Custom SQL query interface (for power users)
- [ ] Pre-built query templates
- [ ] Export query results (CSV, JSON, Parquet)

---

## Phase 5: Release & Deployment

**Goal:** Establish open-source release infrastructure.

### 5.1 GitHub Repository Setup
- [ ] Create comprehensive README.md
- [ ] Add CONTRIBUTING.md guidelines
- [ ] Add LICENSE (MIT/Apache 2.0)
- [ ] Issue templates (bug report, feature request)
- [ ] Pull request template
- [ ] Code of conduct

### 5.2 CI/CD Pipeline (GitHub Actions)
- [ ] **CI:** Run tests on every PR
- [ ] **CI:** Lint and type checking
- [ ] **CI:** Build Docker images
- [ ] **CD:** Deploy to staging on `main` branch
- [ ] **CD:** Deploy to production on release tags

### 5.3 Release Management
- [ ] Semantic versioning (semver)
- [ ] Automated changelog generation (conventional commits)
- [ ] GitHub Releases with:
  - Release notes
  - Pre-built binaries (if applicable)
  - Docker image tags
- [ ] Release checklist template

### 5.4 Docker & Container Deployment
- [ ] Multi-stage Dockerfile (optimized image)
- [ ] Docker Compose for local development
- [ ] Docker Compose for production (with persistence)
- [ ] Environment variable configuration
- [ ] Health checks and graceful shutdown
- [ ] Published to:
  - Docker Hub
  - GitHub Container Registry (ghcr.io)

### 5.5 Deployment Options Documentation
- [ ] Docker single-container deployment
- [ ] Docker Compose deployment guide
- [ ] Kubernetes manifests (optional)
- [ ] Cloud deployment guides (Railway, Fly.io, Render)
- [ ] Self-hosted guide with reverse proxy (nginx/Caddy)

---

## Phase 6: Polish & Extras (Nice-to-Have)

### 6.1 User Experience
- [ ] Dark mode support
- [ ] PWA (Progressive Web App) for offline access
- [ ] Push notifications for schedule changes
- [ ] Accessibility audit (WCAG compliance)
- [ ] Internationalization (i18n)

### 6.2 Advanced Features
- [ ] Compare schedules between years (historical data)
- [ ] AI-powered talk recommendations
- [ ] Social features (share, comment)
- [ ] Live stream integration
- [ ] Post-event video linking

### 6.3 Community
- [ ] Public roadmap page
- [ ] Discord/Matrix community
- [ ] Contributor recognition
- [ ] Plugin/extension system

---

## Tech Stack Recommendation

| Component | Recommendation | Alternatives |
|-----------|---------------|--------------|
| **Backend** | Python + FastAPI | Node.js + Express |
| **Database** | DuckDB (embedded) | - |
| **Scraper** | Python (requests + lxml/BeautifulSoup) | Node.js (cheerio) |
| **Scheduler** | APScheduler / python-crontab | node-cron |
| **Frontend** | React + Vite | Vue, Svelte, HTMX |
| **Charts** | Chart.js / Apache ECharts | D3.js, Plotly |
| **Styling** | Tailwind CSS | CSS Modules, styled-components |
| **Containerization** | Docker + Docker Compose | Podman |
| **CI/CD** | GitHub Actions | GitLab CI, CircleCI |

---

## Milestones

| Milestone | Target | Description |
|-----------|--------|-------------|
| **v0.1.0-alpha** | Week 2 | Scraper working, DuckDB populated, basic API, licensing done |
| **v0.2.0-alpha** | Week 4 | Frontend with search and schedule viewer |
| **v0.3.0-beta** | Week 6 | Analytics dashboard, Docker deployment, attribution UI |
| **v0.4.0-beta** | Week 8 | Personal schedule, iCal export |
| **v1.0.0** | Week 10 | Stable release, full documentation |

---

## Getting Started (Future README Preview)

```bash
# Clone the repository
git clone https://github.com/yourusername/fosdem-explorer.git
cd fosdem-explorer

# Run with Docker Compose
docker-compose up -d

# Or run locally
pip install -r requirements.txt
python -m fosdem_explorer

# Access the app
open http://localhost:8000
```

---

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project uses a **dual-license** approach:

| Component | License | File |
|-----------|---------|------|
| Application code | [MIT License](https://opensource.org/licenses/MIT) | `LICENSE` |
| FOSDEM schedule data | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | `DATA_LICENSE.md` |

Schedule data © FOSDEM. See Phase 0 for full attribution requirements.
