# Bug Report

_Generated: 21 March 2026 — v1.1.0_
_249 Python tests passing · ruff + mypy clean · 28 a11y + 18 smoke Cypress tests passing_

---

### ~~BUG-4: Missing `.catch()` on fetch calls in My Schedule~~ ✅ Fixed

**File:** `src/templates/my_schedule.html`

Two `fetch()` calls (schedule grid load ~line 118, conflict detection ~line 157)
have no `.catch()` handler. Network errors silently leave the page in a broken
or empty state with no user feedback.

**Fix applied:** `.catch()` handlers added to both fetch calls, displaying an
error toast via `showToast()` on network failure.

---

### ~~BUG-5: DuckDB connections have no recovery path~~ ✅ Fixed

**File:** `src/adapters/persistence/duckdb_connection.py`

`DuckDBConnection.get()` caches connections per thread with no TTL or health
check. If the database file is deleted, moved, or becomes corrupt, every
subsequent request on that thread fails indefinitely with no automatic recovery.

**Fix applied:** `get()` now runs `SELECT 1` on any cached connection before
returning it. If the health check raises, the stale connection is closed and
removed, and a fresh connection is created and returned transparently.

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

| Area                                  | Notes                                                 |
| ------------------------------------- | ----------------------------------------------------- |
| `/api/v1/overview` endpoint           | No test exists                                        |
| `build_grid_for_ids()` service method | Called by My Schedule grid route but untested         |
| Health endpoint 503 path              | `except` branch not exercised in tests                |
| Malformed XML in scraper              | No tests for missing or broken XML tags               |
| Concurrent access                     | No thread-safety tests for the DuckDB connection pool |
