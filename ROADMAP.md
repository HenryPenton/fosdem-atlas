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

- [x] Grouped by day
- [x] Sort by time, track, or room
- [x] "Now & Next" highlighting

### 3.2 Timeline/Grid View

- [x] Visual grid: rooms × time slots
- [x] Click cell → event details
- [x] Mobile-responsive

### 3.3 Track Browser

- [x] List all tracks
- [x] Click track → see all events in that track

### 3.4 Speaker Browser

- [x] List all speakers
- [x] Click speaker → see their talks
- [x] Speaker bio if available

**🎯 Deliverable:** Browse schedule by grid, track, or speaker.

---

## Phase 4: Analytics Dashboard

**Goal:** Interesting stats powered by DuckDB.

### 4.1 Basic Stats ✓

- [x] Total events, speakers, tracks, rooms
- [x] Events per day
- [x] Events per track (bar chart)

### 4.2 Room Utilization

- [x] Events per room
- [x] Room usage heatmap (day × hour)

### 4.3 Speaker Stats ✓

- [x] Top speakers by talk count
- [x] Speakers appearing in multiple tracks

### 4.4 Topic Trends ✓

- [x] Word cloud from titles/abstracts
- [x] Most mentioned technologies

### 4.5 Export ✓

- [x] Download stats as CSV

**🎯 Deliverable:** Analytics page with charts and exportable data.

---

## Phase 5: Personal Schedule & Polish

**Goal:** Save favorites, export, polish UX.

### 5.1 Personal Schedule ✓

- [x] Add/remove events to "My Schedule" (localStorage)
- [x] Conflict detection (overlapping times)
- [x] Export to iCal (.ics)

### 5.2 UX Polish

- [x] Dark mode toggle
- [x] Mobile-first responsive tweaks
- [x] Loading states and error handling

### 5.3 Deployment Hardening

- [x] Health check endpoints
- [x] Graceful shutdown
- [x] Production Docker optimizations
- [x] Migrate Dockerfile to multi-stage build to reduce image size
- [x] Add port mapping and resource limits to `docker-compose.yml`

### 5.4 Documentation

- [x] Full README with screenshots
- [x] Self-hosting guide
- [x] CONTRIBUTING.md

### 5.5 Self-Hosting Deploy Snippet

- [x] Add a "Deploy it yourself" section to the homepage with a copyable code block showing the `docker-compose up` quick-start commands
- [x] Syntax-highlighted, one-click copy button

### 5.6 Load Testing

- [x] k6 smoke test covering all key pages and API endpoints
- [x] k6 load test ramping to realistic VU counts with p(95) latency thresholds
- [x] `make load-test` and `make smoke-test` Makefile targets

**🎯 Deliverable:** Production-ready v1.0 release.

---

## Phase 6: Extended Features

**Goal:** Broader reach and accessibility.

### 6.1 Offline

- [x] PWA for offline access

### 6.2 Rate Limiting

- [x] Add global rate limiting with slowapi
- [x] Return 429 responses with `Retry-After` header

### 6.3 UI Fixes & Polish

- [x] Replace emoji star bookmark with consistent SVG icon throughout the app
- [x] Download and store speaker bios from the FOSDEM schedule feed

### 6.4 Performance: Caching

**Phase A — zero-argument calls (highest impact)**

- [x] Cache `ScheduleService.get_overview()` (called on every homepage load)
- [x] Cache `ScheduleService.get_all_tracks_with_counts()` (called on `/tracks`, CSV export, and API)
- [x] Cache `SpeakerService.get_all_speakers()` (called on `/speakers`, CSV export, and API)

**Phase B — small-key-space calls**

- [x] Cache `ScheduleService.get_grid_data(day)` (most expensive computation; ~3 possible day keys)
- [x] Cache `ScheduleService.get_day_detail(day)`
- [x] Cache repository-level `get_unique_days/tracks/rooms()` (called on nearly every page load)

**Phase C — bounded per-item caches (optional)**

- [x] Cache `ScheduleService.get_event_detail(event_id)` with `maxsize=256`
- [x] Cache `SpeakerService.get_speaker_detail(speaker_id)` with `maxsize=256`

### 6.5 Content & Discovery

- [x] Links - store the links section when scraping from FOSDEM and display under the links section in app
- [x] Search/filter on the Speakers page (client-side filter by name)
- [x] Search/filter on the Tracks page (client-side filter by track name)
- [x] 404 pages use `Referer` header to show a context-aware back link

### 6.6 Accessibility

- [ ] Accessibility audit (WCAG)
- [ ] Fix heatmap colour-scale tooltip when all event counts are zero (shows misleading max of 1)

### 6.7 Schedule Grid Layout

- [ ] Use `CSS.escape()` in `toggleHour()` to handle time strings with CSS-special characters

### 6.8 Dependency & CI Hygiene

- [ ] Public roadmap page
- [ ] Pin production dependencies to narrow version ranges for reproducible builds
- [ ] Add Python 3.11 to CI test matrix to verify declared `>=3.11` compatibility
- [ ] Set up Dependabot or Renovate for automated dependency updates

### 6.9 i18n support

- [ ] i18n support

**🎯 Deliverable:** Accessible, offline-capable app with rate limiting.

---

## Phase 7: Push Notifications

**Goal:** Notify users about upcoming talks from their personal schedule via a privately hosted ntfy server.

This phase has its own detailed roadmap: see [NTFY_ROADMAP.md](NTFY_ROADMAP.md).

**🎯 Deliverable:** Subscribers receive per-event, per-track, and per-speaker push notifications with rich actions and schedule-change alerts.

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

| Version    | Phase   | Deliverable                              |
| ---------- | ------- | ---------------------------------------- |
| **v0.1.0** | Phase 1 | Walking skeleton — list all events       |
| **v0.2.0** | Phase 2 | Search & filter, event details           |
| **v0.3.0** | Phase 3 | Grid view, track/speaker browsers        |
| **v0.4.0** | Phase 4 | Analytics dashboard                      |
| **v1.0.0** | Phase 5 | Personal schedule, polish, docs          |
| **v1.1.0** | Phase 6 | PWA, rate limiting, UI fixes, a11y, i18n |
| **v1.2.0** | Phase 7 | Push notifications (see [NTFY_ROADMAP.md](NTFY_ROADMAP.md)) |

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

```
