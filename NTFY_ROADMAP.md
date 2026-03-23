# FOSDEM Notifier — NTFY Roadmap

A privately hosted [ntfy](https://ntfy.sh) instance powering push notifications
for the FOSDEM Explorer app. One authorised publisher (the backend); everyone
else is a read-only subscriber.

---

## Architecture

```
  ScheduleService ─┐
  SpeakerService  ─┤  (cached application services)
  AnalyticsService ┘
        │
        ▼
  NotificationService            (application layer — no direct DB access)
        │
        │  uses NtfyClient adapter
        ▼
  ntfy server                    (self-hosted, Docker)
        │
        ├─ SSE / WebSocket       (ntfy web UI, curl, scripts)
        ├─ UnifiedPush            (Android apps)
        ├─ Web Push               (browsers without the ntfy app)
        └─ Telegram bridge        (optional)
        │
        ▼
  Subscriber devices
```

The `NotificationService` lives in `src/application/` and depends on
`ScheduleService`, `SpeakerService`, and the `NtfyClient` adapter. It never
queries DuckDB directly — all schedule data flows through the existing
services, which already cache expensive queries (overview, grid, tracks,
speakers, event details, etc.). This keeps the notification layer lightweight
and consistent with the rest of the app.

- **Write access** — publisher token only (never exposed to clients).
- **Read access** — anonymous; any subscriber can connect to any topic.
- **ACL** — `deny-all` write by default; explicit `allow` for the publisher.

---

## Topic naming convention

| Pattern | Example | Scope |
| --- | --- | --- |
| `fosdem-event-{id}` | `fosdem-event-8376` | Single event |
| `fosdem-track-{slug}` | `fosdem-track-rust` | All events in a track |
| `fosdem-speaker-{id}` | `fosdem-speaker-1324` | All talks by a speaker |
| `fosdem-room-{slug}` | `fosdem-room-janson` | All events in a room |
| `fosdem-type-{type}` | `fosdem-type-bof` | All events of a given type |
| `fosdem-keynotes` | — | Main Track events only |
| `fosdem-lightning` | — | All lightning talks |
| `fosdem-digest` | — | Morning digests |
| `fosdem-changes` | — | Schedule change alerts |
| `fosdem-media` | — | Video/slides available |
| `fosdem-announcements` | — | Conference open/close, wrap-up |
| `fosdem-all` | — | Everything (high volume) |
| `fosdem-ops` | — | Internal ops alerts |

---

## Phase 1: Walking Skeleton

**Goal:** A running ntfy server that can receive one test message from the
backend and deliver it to a subscriber.

### 1.1 Infrastructure

- [ ] Add `ntfy` service to `docker-compose.yml` with a named volume for cache persistence
- [ ] Write `ntfy/server.yml` — base URL, cache duration, attachment settings
- [ ] Expose ntfy only on the internal Docker network; reverse-proxy via the existing web server
- [ ] Store the publisher token as a Docker secret / environment variable — never commit to source
- [ ] Configure ntfy ACL: anonymous read-only, publisher token write-only

### 1.2 Publisher adapter

- [ ] Add `NTFY_BASE_URL` and `NTFY_PUBLISHER_TOKEN` to `src/config.py` (both optional — app runs without them)
- [ ] Define `Notifier` port in `src/domain/ports.py` — `publish(topic, title, body, **kwargs)` protocol
- [ ] Create `src/adapters/notifier/ntfy_client.py` — async `httpx` implementation of `Notifier`
- [ ] Support ntfy fields: `priority`, `tags`, `click`, `actions`, `attach`, `markdown`
- [ ] Unit-test with a mocked `httpx` transport

### 1.3 Notification service

- [ ] Create `src/application/notification_service.py`
- [ ] Constructor takes `ScheduleService`, `SpeakerService`, and the `Notifier` port — no repository or DuckDB dependency
- [ ] All schedule data accessed via services (benefiting from in-memory caches)
- [ ] Wire into `src/main.py` alongside the other services

### 1.4 Smoke test

- [ ] `make notify-test` publishes a test message to `fosdem-announcements`
- [ ] Verify delivery in the ntfy web UI and via the mobile app

**🎯 Deliverable:** `make notify-test` sends a message that any ntfy subscriber receives.

---

## Phase 2: Event Reminders

**Goal:** Subscribers receive a push notification before a talk they follow starts.

### 2.1 Reminder scheduler

- [ ] APScheduler job runs every minute, calls `NotificationService.send_upcoming_reminders()`
- [ ] Service uses `ScheduleService.get_day_detail(day)` (cached) to find events starting within the reminder window
- [ ] Publishes to `fosdem-event-{id}` for each match via the `Notifier` port
- [ ] Reminder horizon configurable (`NOTIFY_REMIND_MINUTES`, default `10`)

### 2.2 Duration-aware timing

- [ ] Short events (≤10 min — lightning talks) use a longer reminder window (15 min) so subscribers have time to walk over
- [ ] Workshops (the 8-hour soldering workshop, etc.) get an additional early reminder at 30 min

### 2.3 Notification content

- [ ] Event detail fetched via `ScheduleService.get_event_detail(event_id)` (cached, maxsize 256)
- [ ] Title: `Starting in {N} min — {talk title}`
- [ ] Body: room, track, speaker names (cap at 3 names + "and N others" for multi-speaker events like "Lightning lightning talks 2" with 13 speakers)
- [ ] Click URL: `/event/{id}`
- [ ] Tags: `calendar`, track slug
- [ ] Priority: `high`

### 2.4 De-duplication

- [ ] In-memory set tracks `(event_id, reminder_horizon)` pairs already sent this session
- [ ] Persisted to a `notifications_sent` table (via a small `NotificationLogRepository` port) so state survives restarts
- [ ] Prevents double-sends after restarts or scheduler overlap

### 2.5 Event page integration

- [ ] Event detail page shows the ntfy topic name with a subscribe link
- [ ] Deep link format: `ntfy://{base}/fosdem-event-{id}`

**🎯 Deliverable:** Subscribe to `fosdem-event-8376`; receive a notification 10 minutes before "Welcome to FOSDEM 2026".

---

## Phase 3: Track, Speaker, Room & Type Subscriptions

**Goal:** Coarse-grained subscriptions — follow a whole track, a speaker, a
room, or an event type without managing individual event topics.

### 3.1 Track topics

- [ ] Publish to `fosdem-track-{slug}` (71 tracks) for every event in that track
- [ ] Track list sourced from `ScheduleService.get_all_tracks_with_counts()` (cached)
- [ ] Track page shows the topic name and subscribe link
- [ ] Body includes event title, start time, room, and speaker names

### 3.2 Speaker topics

- [ ] Publish to `fosdem-speaker-{id}` (1,216 speakers; 193 give multiple talks)
- [ ] Speaker list sourced from `SpeakerService.get_all_speakers()` (cached)
- [ ] Speaker detail page shows the topic name and subscribe link
- [ ] Each talk by a speaker gets its own notification

### 3.3 Room topics

- [ ] Publish to `fosdem-room-{slug}` (37 rooms) for every event in that room
- [ ] Room list sourced from `ScheduleService.get_unique_rooms()` (cached)
- [ ] Useful for attendees who park in one room all day (e.g. Janson)
- [ ] Room slug derived from the room name (lowercase, hyphens for spaces)

### 3.4 Event type topics

- [ ] `fosdem-type-bof` — all 66 BOFs (informal meetups that are easy to miss)
- [ ] `fosdem-type-workshop` — workshops with limited capacity (arrive early!)
- [ ] `fosdem-type-lightningtalk` — all 23 lightning talks
- [ ] `fosdem-type-maintrack` — all 45 main-track talks
- [ ] `fosdem-type-junior` — all 18 junior-track talks
- [ ] `fosdem-type-devroom` — firehose of all 926 devroom talks (documented as high-volume)

### 3.5 Keynote & lightning talk topics

- [ ] `fosdem-keynotes` receives reminders for all Main Track and Main Track (K-building) events
- [ ] `fosdem-lightning` receives reminders when each lightning-talk block starts, with the full lineup in the body

### 3.6 Catch-all topic

- [ ] `fosdem-all` mirrors every notification — documented as very high volume (~1,079 events)

### 3.7 Topic directory page

- [ ] `/notifications` page lists all available topics grouped by category (events, tracks, speakers, rooms, types)
- [ ] Each row shows the topic name, a one-click subscribe link (`ntfy://…`), and a QR code
- [ ] Client-side search box filters topics in real-time

**🎯 Deliverable:** Subscribe to `fosdem-track-rust` and get notified before every Rust talk.

---

## Phase 4: Schedule Change Alerts

**Goal:** Subscribers learn immediately when the schedule changes — room moves,
cancellations, new talks added.

### 4.1 Change detection

- [ ] `NotificationService` snapshots the current schedule via `ScheduleService` before each scrape
- [ ] After the scrape (and cache invalidation), it re-fetches from `ScheduleService` and diffs against the snapshot
- [ ] Detect: room changed, time changed, talk cancelled, new talk added, speaker changed, duration changed

### 4.2 Change notifications

- [ ] Room change: `Room change — {title} moved to {new_room}` (priority `urgent`)
- [ ] Time change: `Time change — {title} now at {new_time}` (priority `urgent`)
- [ ] Cancellation: `Cancelled — {title}` (priority `urgent`)
- [ ] New talk added: `New — {title}` (priority `default`)
- [ ] Speaker change: `Speaker update — {title}` (priority `default`)
- [ ] Publish to the matching event, track, speaker, and room topics, plus `fosdem-changes`

### 4.3 Conflict re-check

- [ ] When a time or room changes, re-check for scheduling conflicts with other events on the same topic subscriptions
- [ ] Notify if a change creates a new overlap: `Conflict — {title A} and {title B} now overlap`

### 4.4 Change log

- [ ] Detected changes persisted via a `ScheduleChangeRepository` port (DuckDB `schedule_changes` table)
- [ ] New `ScheduleChangeService` exposes change history — keeps the web layer going through services, not raw DB
- [ ] `/schedule-changes` page shows changes in reverse-chronological order
- [ ] Filterable by track, room, and change type

**🎯 Deliverable:** Subscribers receive an urgent notification if a talk moves room or is cancelled.

---

## Phase 5: Rich Notifications & Actions

**Goal:** Notifications are actionable — subscribers can open the app, join the
chat, add to calendar, or snooze without leaving the notification.

### 5.1 Action buttons

- [ ] "View" → opens `/event/{id}` in the browser
- [ ] "Calendar" → downloads the `.ics` file for that event
- [ ] "Chat" → opens the event's Matrix chat room (every event has one)
- [ ] "Snooze 5 min" → publisher re-schedules a follow-up notification 5 minutes later

### 5.2 Chat room integration

- [ ] Include the Matrix chat room URL (from the `<links>` element) in every reminder notification
- [ ] Useful for remote attendees following along in the chat

### 5.3 Markdown body

- [ ] Use ntfy Markdown for structured body: **room**, **time**, *speakers*
- [ ] For multi-speaker events (up to 13 speakers), show first 3 names + "and N more"
- [ ] Plain-text fallback for clients without Markdown support

### 5.4 Notification card image

- [ ] Generate a small card image (title, time, room) server-side with Pillow or SVG
- [ ] Attach via ntfy's attachment feature
- [ ] Makes notifications visually distinct in crowded notification centres

### 5.5 Priority policy

| Scenario | Priority |
| --- | --- |
| Reminder > 15 min | `default` |
| Reminder ≤ 15 min | `high` |
| Cancellation, room change, time change | `urgent` |
| New talk, speaker change | `default` |
| Digest, media available | `low` |

**🎯 Deliverable:** Tappable "View", "Calendar", and "Chat" buttons on every notification.

---

## Phase 6: Post-Talk & Media Notifications

**Goal:** Subscribers are notified after a talk ends — feedback reminder, slides
uploaded, video recording available.

### 6.1 Feedback reminder

- [ ] 5 minutes after a talk ends, publish a reminder to submit feedback
- [ ] Event detail (including `feedback_url`) fetched via `ScheduleService.get_event_detail(id)` (cached)
- [ ] Title: `How was it? — {talk title}`
- [ ] Priority: `low`

### 6.2 Slides available

- [ ] After each scrape, `NotificationService` compares event links/attachments before and after cache invalidation
- [ ] When a new `slides` attachment appears, publish to the event topic
- [ ] Title: `Slides posted — {talk title}`
- [ ] Click URL: direct link to the PDF
- [ ] Also publish to `fosdem-media`

### 6.3 Video recording available

- [ ] When a scrape cycle detects a new video link (via `ScheduleService.get_event_detail()` diff), publish to the event topic
- [ ] Title: `Recording available — {talk title}`
- [ ] Body: AV1/WebM link (preferred) and MP4 link (legacy)
- [ ] Click URL: the AV1/WebM video URL
- [ ] Also publish to `fosdem-media`

### 6.4 Subtitle file available

- [ ] When a `.vtt` subtitle link appears, publish to the event topic
- [ ] Title: `Subtitles added — {talk title}`
- [ ] Useful for non-native English speakers and accessibility

**🎯 Deliverable:** After a talk, subscribers are nudged to give feedback and later notified when slides and recordings land.

---

## Phase 7: Digests & Announcements

**Goal:** Scheduled summary notifications so subscribers can plan ahead without
being overwhelmed.

### 7.1 Morning digest

- [ ] Published to `fosdem-digest` at 08:00 CET on each conference day
- [ ] Day data from `ScheduleService.get_day_detail(day)` (cached); track sizes from `get_all_tracks_with_counts()` (cached)
- [ ] Lists the day's keynotes and the five largest tracks by event count
- [ ] Links to the day view in the app

### 7.2 Keynote reminders

- [ ] `fosdem-keynotes` receives a reminder before each Main Track and Main Track (K-building) event
- [ ] Includes the opening talk ("Welcome to FOSDEM 2026") and closing talk ("Closing FOSDEM 2026")

### 7.3 BOF & workshop highlights

- [ ] Morning digest includes a "BOFs today" section (up to 30+ BOFs per day)
- [ ] Workshop events get a highlighted callout with early-arrival advice

### 7.4 Hourly "happening now"

- [ ] `fosdem-now` topic receives a summary at the top of each hour during the conference
- [ ] Built from `ScheduleService.get_day_detail(day)` (cached) filtered to the current hour
- [ ] Lists all talks starting in the next 60 minutes, grouped by building
- [ ] Useful for attendees wandering between rooms

### 7.5 Conference opening & closing

- [ ] `fosdem-announcements` fires when the conference officially opens (first keynote) and closes (final talk)
- [ ] Opening notification includes a link to the day 1 schedule
- [ ] Closing notification includes a "thank you" message

### 7.6 Post-conference wrap-up

- [ ] After the final session, publish a summary to `fosdem-announcements`
- [ ] Stats sourced from `AnalyticsService.get_analytics()` (cached): total events, unique speakers, most popular track, total tracks and rooms
- [ ] Link to the analytics page

**🎯 Deliverable:** Subscribers get one morning digest per day plus hourly summaries during the conference.

---

## Phase 8: Subscriber Experience & Discovery

**Goal:** Make it effortless for attendees to find and manage their subscriptions.

### 8.1 Notifications page

- [ ] `/notifications` page lists all topics grouped by type
- [ ] Client-side search filters by topic name, track, speaker, or room
- [ ] Each row shows: topic name, description, estimated volume (low / medium / high)

### 8.2 One-tap subscribe

- [ ] `ntfy://` deep links open the ntfy app directly on Android/iOS
- [ ] Fallback "copy topic name" button for users who prefer the ntfy web UI or CLI

### 8.3 QR codes

- [ ] Each topic on `/notifications` has a QR code linking to the subscription URL
- [ ] Generated server-side with the `qrcode` library and cached
- [ ] Scannable from a printed schedule or a friend's screen

### 8.4 In-page subscribe banners

- [ ] Event detail page: banner with "Get notified" linking to `fosdem-event-{id}`
- [ ] Track page: banner with "Follow this track" linking to `fosdem-track-{slug}`
- [ ] Speaker page: banner with "Follow this speaker" linking to `fosdem-speaker-{id}`
- [ ] Banners dismissable; preference remembered in `localStorage`

### 8.5 ntfy web UI

- [ ] ntfy web UI proxied at `/ntfy/` for browser-only subscribers
- [ ] `web-push-public-key` configured so browser push works without the native app

### 8.6 Telegram bridge (optional)

- [ ] ntfy Telegram bridge forwards `fosdem-announcements` and `fosdem-keynotes` to a public Telegram channel
- [ ] Setup documented in `SELF_HOSTING.md`

### 8.7 My Schedule integration

- [ ] When a user adds an event to "My Schedule" (localStorage), show a prompt to subscribe to the matching ntfy topic
- [ ] Bulk-subscribe link: generate a single `ntfy://` URL that subscribes to all events in the user's personal schedule

**🎯 Deliverable:** Any attendee can find and subscribe to topics in under 30 seconds.

---

## Phase 9: Conflict & Overlap Alerts

**Goal:** Help attendees manage the chaos of 1,000+ events across 37 rooms.

### 9.1 Same-slot conflict notification

- [ ] When multiple events a subscriber follows start at the same time, send a conflict alert
- [ ] Title: `Conflict — {N} talks at {time}`
- [ ] Body lists the conflicting talks with room and track

### 9.2 "About to end" alert

- [ ] Optional notification 5 minutes before a talk ends, useful for planning the walk to the next room
- [ ] Enabled per-topic via a separate `fosdem-ending-{id}` topic (opt-in, not default)

### 9.3 Room proximity hints

- [ ] If two consecutive subscribed talks are in different buildings (e.g. Janson → K.3.201), the reminder for the second talk includes a note: "different building — allow extra travel time"
- [ ] Building inferred from the room name prefix (H, K, AW, UA, UB, UD)

**🎯 Deliverable:** Subscribers are warned about scheduling conflicts and building changes between talks.

---

## Phase 10: Operations, Reliability & Observability

**Goal:** The notification system is production-hardened, monitored, and
recoverable.

### 10.1 Health & liveness

- [ ] Poll ntfy `/v1/health` from the FOSDEM Explorer health check
- [ ] If ntfy is unreachable, the scheduler logs a warning but does not crash
- [ ] Health surfaced on `/health` as `ntfy: ok | degraded | unavailable`

### 10.2 Metrics

- [ ] Enable ntfy Prometheus endpoint (`metrics-listen-http`)
- [ ] Application-level metrics: notifications sent (by topic type), change alerts fired, scheduler lag
- [ ] Grafana dashboard JSON committed to `monitoring/`

### 10.3 Alerting

- [ ] Alert if ntfy unreachable for > 5 min
- [ ] Alert if scheduler job has not run in > 2 min
- [ ] Delivered via `fosdem-ops` topic — self-contained within the stack

### 10.4 Persistence & backup

- [ ] ntfy cache and attachments in a named Docker volume
- [ ] Daily snapshot to object storage or backup volume
- [ ] Restore procedure documented in `SELF_HOSTING.md`

### 10.5 Rate limiting & abuse prevention

- [ ] ntfy `visitor-*` settings tuned to prevent subscriber flooding
- [ ] Publisher token rotatable via environment variable without restart
- [ ] ACL enforced: only the publisher token can write; everyone else read-only

### 10.6 Log management

- [ ] Logs forwarded to the same aggregator as the main app
- [ ] Retention: 7 days default
- [ ] IP addresses redacted by default

### 10.7 Load testing

- [ ] k6 script simulates publishing 1,079 notifications (one per event) in rapid succession
- [ ] Verify ntfy throughput and memory usage under load
- [ ] Document recommended resource limits for Docker Compose

**🎯 Deliverable:** The notification service is monitored, alerting, and recoverable with no manual state reconstruction.

---

## Tech Stack

| Component | Technology |
| --- | --- |
| **Notification server** | ntfy (self-hosted, Docker) |
| **Publisher client** | Python + httpx (async) |
| **Scheduler** | APScheduler (existing) |
| **Card image generation** | Pillow / SVG |
| **QR codes** | `qrcode` Python library |
| **Containerisation** | Docker + Docker Compose |
| **Metrics** | Prometheus + Grafana |
| **Telegram bridge** | ntfy built-in (optional) |

---

## Milestones

| Version | Phase | Deliverable |
| --- | --- | --- |
| **v0.1** | Phase 1 | ntfy running; test message delivered |
| **v0.2** | Phase 2 | Per-event reminders before talks start |
| **v0.3** | Phase 3 | Track, speaker, room, and type subscriptions |
| **v0.4** | Phase 4 | Schedule change alerts |
| **v0.5** | Phase 5 | Rich notifications with action buttons and chat links |
| **v0.6** | Phase 6 | Post-talk feedback and media-available notifications |
| **v0.7** | Phase 7 | Morning digests, hourly summaries, announcements |
| **v0.8** | Phase 8 | Subscriber discovery UX and My Schedule integration |
| **v0.9** | Phase 9 | Conflict and overlap alerts |
| **v1.0** | Phase 10 | Production-hardened, monitored, load-tested |

---

## Security model

- The publisher token is a server-side secret stored in an environment
  variable or Docker secret. It is never sent to the browser or included in
  any client-facing response.
- All ntfy topics are read-only for unauthenticated subscribers (ntfy ACL:
  `deny-all` write; explicit `allow` for the publisher token only).
- The ntfy service is not exposed on a public port; all traffic is proxied
  through the existing reverse proxy with TLS termination.
- Subscriber IP addresses are not logged by default;
  `visitor-subscription-limit` prevents resource exhaustion.
- The publisher token can be rotated without downtime by updating the
  environment variable and reloading the ntfy ACL.
