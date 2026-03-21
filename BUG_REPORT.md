# Bug Report

_Generated: 21 March 2026 — v2.1.0_
_269 Python tests passing · ruff + mypy clean · 28 a11y + 18 smoke Cypress tests passing_


---

## High

### BUG-5: CSV injection in API export endpoint

**File:** `src/api/routers/export.py`

The API CSV export (`/api/v1/export/events.csv`, `/api/v1/export/speakers.csv`)
writes event titles and abstracts directly to CSV without sanitisation. Values
starting with `=`, `+`, `-`, or `@` are interpreted as formulas by spreadsheet
applications. The web export endpoint (`src/adapters/web/routers/export.py`)
already protects against this with `_sanitise_csv_value()`, but the API
endpoint has no equivalent.

**Fix:** Apply the same `_sanitise_csv_value()` sanitisation in
`src/api/routers/export.py`'s `_csv_response()`, or extract it to a shared
utility.

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

### BUG-6: Conflict detection only warns for different rooms

**File:** `src/static/js/my-schedule.js:71-73`

`detectConflicts()` skips overlapping events in the same room
(`if (parsed[i].room !== parsed[j].room)`). The comment says "same room isn't
a conflict the user can control", but the logic is inverted — same-room
overlaps are the *most* impossible to attend, while different-room overlaps
might be manageable. Users are warned about the wrong set of conflicts.

**Fix:** Remove the room check so all temporal overlaps are reported, or
reverse the condition to warn about same-room overlaps.

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
| API CSV export sanitisation           | No test verifies formula-injection protection         |
| Conflict detection logic              | No test for `detectConflicts()` same-room behaviour   |
