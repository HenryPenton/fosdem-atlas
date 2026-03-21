# Bug Report

_Generated: 21 March 2026 — v1.1.0_
_249 Python tests passing · ruff + mypy clean · 28 a11y + 18 smoke Cypress tests passing_

---

## Critical

### ~~BUG-1: XSS — `| safe` renders unsanitised HTML from FOSDEM abstracts~~ ✅ Fixed

**Files:** `src/templates/event.html:51`, `src/templates/partials/event_card.html:21`

Event abstracts from the FOSDEM XML feed are rendered with Jinja2's `| safe`
filter, bypassing auto-escaping. The scraper performs no HTML sanitisation on
abstract content. While FOSDEM is a trusted data source, a modified or
compromised XML feed could inject `<script>` tags that execute in users'
browsers.

**Fix applied:** `nh3` added as a production dependency. Abstracts are now
sanitised via `FosdemScheduleFetcher._sanitise_html()` at ingestion time using
an allowlist of safe formatting tags. The stored content is clean before it
ever reaches the `| safe` filter.

---

### ~~BUG-2: CSV formula injection in event export~~ ✅ Fixed

**File:** `src/adapters/web/routers/export.py`

The CSV export writes `event.abstract` directly into cells with no escaping.
Abstracts starting with `=`, `+`, `-`, or `@` trigger formula execution when
opened in Excel or Google Sheets.

**Fix applied:** `_sanitise_csv_value()` helper added in `export.py`. All string
cell values are checked before writing; any value whose first character is a
formula-trigger (`=`, `+`, `-`, `@`) is prefixed with a tab character.

---

## High

### BUG-3: No security response headers

**File:** `src/adapters/web/app.py`

The app sets no `Content-Security-Policy`, `X-Frame-Options`,
`X-Content-Type-Options`, or `Strict-Transport-Security` headers. Pages can be
iframed by third-party sites (clickjacking) and responses are subject to MIME
content-sniffing.

**Fix:** Add a middleware that sets at minimum:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

---

### BUG-4: Missing `.catch()` on fetch calls in My Schedule

**File:** `src/templates/my_schedule.html`

Two `fetch()` calls (schedule grid load ~line 118, conflict detection ~line 157)
have no `.catch()` handler. Network errors silently leave the page in a broken
or empty state with no user feedback.

**Fix:** Add `.catch()` handlers that display an error toast via the existing
`showToast()` helper.

---

### BUG-5: DuckDB connections have no recovery path

**File:** `src/adapters/persistence/duckdb_connection.py`

`DuckDBConnection.get()` caches connections per thread with no TTL or health
check. If the database file is deleted, moved, or becomes corrupt, every
subsequent request on that thread fails indefinitely with no automatic recovery.

**Fix:** Add a lightweight health check (e.g. `SELECT 1`) in `get()` before
returning a cached connection, and re-create on failure.

---

## Medium

### ~~BUG-6: Inconsistent `EventSummary` construction — abstract sometimes missing~~ ✅ Fixed

**File:** `src/adapters/persistence/duckdb_events_repository.py`

`get_all_events()` constructs `EventSummary` without the `abstract` field (it
defaults to `""`), but `get_events_by_day_and_track()` and
`get_events_by_track()` include it. Templates receiving events from different
code paths may see empty abstracts for the same event depending on which service
method was called.

**Fix applied:** `abstract` added to the SELECT and `EventSummary` construction
in `get_all_events()`. All code paths now return the abstract consistently.

---

### BUG-7: Schedule grid hour rows not keyboard-accessible

**File:** `src/templates/partials/schedule_grid.html:31`

`<tr class="grid-hour-header" onclick="toggleHour(this)">` has no `tabindex`,
`role="button"`, or `onkeydown` handler. Keyboard-only users cannot
expand/collapse hour sections in the schedule grid.

**Fix:** Add `tabindex="0"` and an `onkeydown` handler for Enter/Space, or
place a `<button>` inside the row cell.

---

### BUG-8: Analytics tabs missing ARIA connections

**File:** `src/templates/analytics.html`

Tab buttons have `role="tab"` but lack `aria-controls`. Tab panels have
`role="tabpanel"` but lack `aria-labelledby`. Screen readers cannot associate
buttons with their panels.

**Fix:** Add `aria-controls="panel-id"` to each tab button and
`aria-labelledby="button-id"` to each tab panel.

---

### BUG-9: Health endpoint silently swallows exceptions

**File:** `src/adapters/web/routers/health.py`

`except Exception` catches and discards all errors without logging. Silent
failures make production debugging and alerting impossible.

**Fix:** Add `logging.exception()` or `logging.error()` inside the except
block.

---

### BUG-10: ILIKE wildcards in user search input not escaped

**File:** `src/adapters/persistence/duckdb_events_repository.py`

`filter_events()` and `search_events()` use `f"%{q}%"` for ILIKE matching.
User input containing `%` or `_` is treated as SQL wildcards, producing
incorrect search results (e.g. searching for `100%` matches everything).

Not a SQL injection risk (queries are parameterised), but a correctness bug.

**Fix:** Escape `%` and `_` in the search term before wrapping with `%…%`.

---

## Low

### BUG-11: 404 pages return plain text instead of styled HTML

**Files:** `src/adapters/web/routers/schedule.py`, `src/adapters/web/routers/speakers.py`

When an event or speaker is not found, the route returns
`Response(content="…not found", status_code=404)` — raw text with no page
layout. Users see unstyled text instead of a branded error page.

**Fix:** Return a template response using a 404 template or `base.html` with
an error message block.

---

### BUG-12: Speakers without events excluded from speakers listing

**File:** `src/adapters/persistence/duckdb_speakers_repository.py`

`get_all_speakers()` uses `JOIN event_speakers`, so speakers with zero
associated events are silently dropped. This may be intentional but is
undocumented.

**Fix:** Document the decision, or use `LEFT JOIN` if orphaned speakers should
appear.

---

## Test Coverage Gaps

| Area | Notes |
| ---- | ----- |
| `/api/v1/overview` endpoint | No test exists |
| `build_grid_for_ids()` service method | Called by My Schedule grid route but untested |
| Health endpoint 503 path | `except` branch not exercised in tests |
| Malformed XML in scraper | No tests for missing or broken XML tags |
| Concurrent access | No thread-safety tests for the DuckDB connection pool |
