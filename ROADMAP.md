# FOSDEM Explorer Roadmap

A DuckDB-powered web application for exploring, searching, and analyzing the FOSDEM 2026 schedule.

## 🎯 Project Vision

Build an open-source tool that scrapes the FOSDEM schedule, stores it in DuckDB for fast analytics, and provides an intuitive interface for attendees to discover talks and gain insights into conference trends.

---

## Phase 1: Walking Skeleton

**Goal:** End-to-end working app — scrape → store → display. Minimal but functional.

### 1.1 Project Setup ✓

- [x] Repository structure (`src/`, `scraper/`, `db/`, `docker/`)
- [x] Tech stack: Python + FastAPI + DuckDB + HTMX
- [x] Makefile, linting, pre-commit

### 1.2 Licensing ✓

- [x] Add `LICENSE` (MIT)
- [x] Add `DATA_LICENSE.md` (FOSDEM data is CC BY 4.0)
- [x] Footer attribution in templates

### 1.3 Basic Scraper ✓

- [x] Fetch FOSDEM XML schedule (https://fosdem.org/2026/schedule/xml)
- [x] Parse events: id, title, start/end time, room, track
- [x] Run manually via CLI command (`make scrape`)

### 1.4 Basic DuckDB ✓

- [x] Single `events` table (id, title, start_time, end_time, room, track)
- [x] Insert scraped events
- [x] Basic query to list all events

### 1.5 Basic Web Page ✓

- [x] Homepage lists all events from DuckDB
- [x] Each event shows: title, time, room, track
- [x] HTMX loads event list
- [x] Footer with FOSDEM attribution

### 1.6 Docker & First Release

- [x] Dockerfile that runs the app
- [x] `docker-compose.yml` with volume for DuckDB persistence
- [x] GitHub Actions: lint + test on push
- [x] Tag `v0.1.0` → build and push Docker image

**🎯 Deliverable:** `docker-compose up` shows a page listing all FOSDEM events.

---

## Phase 2: Search & Filter

**Goal:** Find talks you care about.

### 2.1 Enhanced Scraper

- [x] Parse additional fields: abstract, subtitle, speakers, links
- [x] Store speakers in separate table with `event_speakers` join
- [x] Scheduled scraping every 5 minutes (APScheduler)

### 2.2 Search API & UI

- [x] `/api/events/search?q=...` endpoint
- [x] Full-text search on title + abstract
- [x] Search bar on homepage with HTMX live results

### 2.3 Filter by Track/Room/Day

- [x] Filter dropdowns (track, room, day)
- [x] API supports filter params
- [x] Results update via HTMX

### 2.4 Event Detail Page

- [x] `/event/{id}` page with full abstract
- [x] Speaker names and links
- [x] Link to original FOSDEM page

**🎯 Deliverable:** Search "Rust" → see all Rust talks, click through to details.

---

## Phase 3: Schedule Views

**Goal:** Multiple ways to browse the schedule.

### 3.1 List View (Enhanced)

- [ ] Grouped by day
- [ ] Sort by time, track, or room
- [ ] "Now & Next" highlighting

### 3.2 Timeline/Grid View

- [ ] Visual grid: rooms × time slots
- [ ] Click cell → event details
- [ ] Mobile-responsive

### 3.3 Track Browser

- [ ] List all tracks
- [ ] Click track → see all events in that track
- [ ] Track description if available

### 3.4 Speaker Browser

- [ ] List all speakers
- [ ] Click speaker → see their talks
- [ ] Speaker bio if available

**🎯 Deliverable:** Browse schedule by grid, track, or speaker.

---

## Phase 4: Analytics Dashboard

**Goal:** Interesting stats powered by DuckDB.

### 4.1 Basic Stats

- [ ] Total events, speakers, tracks, rooms
- [ ] Events per day
- [ ] Events per track (bar chart)

### 4.2 Room Utilization

- [ ] Events per room
- [ ] Room usage heatmap (day × hour)

### 4.3 Speaker Stats

- [ ] Top speakers by talk count
- [ ] Speakers appearing in multiple tracks

### 4.4 Topic Trends

- [ ] Word cloud from titles/abstracts
- [ ] Most mentioned technologies

### 4.5 Export

- [ ] Download stats as CSV
- [ ] Raw SQL query interface (power users)

**🎯 Deliverable:** Analytics page with charts and exportable data.

---

## Phase 5: Personal Schedule & Polish

**Goal:** Save favorites, export, polish UX.

### 5.1 Personal Schedule

- [ ] Add/remove events to "My Schedule" (localStorage)
- [ ] Conflict detection (overlapping times)
- [ ] Export to iCal (.ics)

### 5.2 UX Polish

- [ ] Dark mode toggle
- [ ] Mobile-first responsive tweaks
- [ ] Loading states and error handling

### 5.3 Deployment Hardening

- [ ] Health check endpoints
- [ ] Graceful shutdown
- [ ] Production Docker optimizations

### 5.4 Documentation

- [ ] Full README with screenshots
- [ ] Self-hosting guide
- [ ] CONTRIBUTING.md

**🎯 Deliverable:** Production-ready v1.0 release.

---

## Backlog (Nice-to-Have)

- [ ] PWA for offline access
- [ ] Push notifications via NTFY
- [ ] Post-event video links
- [ ] Accessibility audit (WCAG)
- [ ] i18n support
- [ ] Public roadmap page

---

## Tech Stack

| Component            | Technology              |
| -------------------- | ----------------------- |
| **Backend**          | Python + FastAPI        |
| **Database**         | DuckDB (embedded)       |
| **Scraper**          | Python (httpx + lxml)   |
| **Scheduler**        | APScheduler             |
| **Frontend**         | HTMX + Jinja2           |
| **Styling**          | Vanilla CSS             |
| **Containerization** | Docker + Docker Compose |
| **CI/CD**            | GitHub Actions          |

---

## Milestones

| Version    | Phase   | Deliverable                        |
| ---------- | ------- | ---------------------------------- |
| **v0.1.0** | Phase 1 | Walking skeleton — list all events |
| **v0.2.0** | Phase 2 | Search & filter, event details     |
| **v0.3.0** | Phase 3 | Grid view, track/speaker browsers  |
| **v0.4.0** | Phase 4 | Analytics dashboard                |
| **v1.0.0** | Phase 5 | Personal schedule, polish, docs    |

# Access the app

open http://localhost:8000

```

---

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project uses a **dual-license** approach:

| Component            | License                                                   | File              |
| -------------------- | --------------------------------------------------------- | ----------------- |
| Application code     | [MIT License](https://opensource.org/licenses/MIT)        | `LICENSE`         |
| FOSDEM schedule data | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | `DATA_LICENSE.md` |

Schedule data © FOSDEM. See Phase 0 for full attribution requirements.
```
