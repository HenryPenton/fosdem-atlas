# Bug Report

_Generated: 21 March 2026 — v2.1.0_
_269 Python tests passing · ruff + mypy clean · 28 a11y + 18 smoke Cypress tests passing_


---

## High

### ~~BUG-5: CSV injection in API export endpoint~~ ✅ Fixed

**File:** `src/api/routers/export.py`

The API CSV export (`/api/v1/export/events.csv`, `/api/v1/export/speakers.csv`)
wrote event titles and abstracts directly to CSV without sanitisation.

**Fix applied:** `_sanitise_csv_value()` and `_csv_response()` extracted into
`src/adapters/csv_utils.py`. Both export modules now import `sanitise_csv_value`
and `csv_streaming_response` from there. Unit tests added in
`tests/test_csv_utils.py`.

---

## Medium

### BUG-1: Schedule grid hour rows not keyboard-accessible

**File:** `src/templates/partials/schedule_grid.html:31`

`<tr class="grid-hour-header" onclick="toggleHour(this)">` has no `tabindex`,
`role="button"`, or `onkeydown` handler. Keyboard-only users cannot
expand/collapse hour sections in the schedule grid.

**Fix:** Add `tabindex="0"` and an `onkeydown` handler for Enter/Space, or
place a `<button>` inside the row cell.

---

### BUG-2: Analytics tabs missing ARIA connections

**File:** `src/templates/analytics.html`

Tab buttons have `role="tab"` but lack `aria-controls`. Tab panels have
`role="tabpanel"` but lack `aria-labelledby`. Screen readers cannot associate
buttons with their panels.

**Fix:** Add `aria-controls="panel-id"` to each tab button and
`aria-labelledby="button-id"` to each tab panel.

---

### BUG-3: ILIKE wildcards in user search input not escaped

**File:** `src/adapters/persistence/duckdb_events_repository.py`

`filter_events()` and `search_events()` use `f"%{q}%"` for ILIKE matching.
User input containing `%` or `_` is treated as SQL wildcards, producing
incorrect search results (e.g. searching for `100%` matches everything).

Not a SQL injection risk (queries are parameterised), but a correctness bug.

**Fix:** Escape `%` and `_` in the search term before wrapping with `%…%`.

---

## Low

### BUG-4: Speakers without events excluded from speakers listing

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
| Malformed XML in scraper              | No tests for missing or broken XML tags               |
| Concurrent access                     | No thread-safety tests for the DuckDB connection pool |
