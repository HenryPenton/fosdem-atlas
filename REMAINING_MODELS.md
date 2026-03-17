# Remaining Models to Define

Methods in `src/domain/ports.py` that still return raw dicts instead of domain models.

---

## Event-related (could reuse/extend `EventSummary`)

1. **`EventRepository.get_all_events()`** — returns `list[dict]` with keys: `id`, `title`, `start_time`, `duration_minutes`, `room`, `track`, `day`. This is exactly the existing `EventSummary` minus `subtitle`. Either reuse `EventSummary` (with subtitle empty) or create an `EventListItem`.

2. **`EventRepository.get_events_by_day()`** — same shape as `get_all_events()` above.

3. **`EventRepository.get_events_by_day_and_track()`** — returns `list[dict]` with keys: `id`, `title`, `subtitle`, `abstract`, `start_time`, `duration_minutes`, `room`, `track`, `day`. Matches existing `EventSummary` plus `abstract`. Could extend `EventSummary` with an optional `abstract` field or create a new model.

4. **`EventRepository.get_events_by_track()`** — same shape as `get_events_by_day_and_track()` above.

5. **`EventRepository.get_events_by_ids()`** — returns `list[dict]` with keys: `id`, `title`, `subtitle`, `abstract`, `start_time`, `duration_minutes`, `room`, `track`, `day`, `fosdem_url`. Same shape as `EventDetail` (minus `speakers`). Could reuse `EventDetail`.

6. **`EventRepository.filter_events()`** — returns `list[dict]` with keys: `id`, `title`, `abstract`, `start_time`, `duration_minutes`, `room`, `track`, `day`. Same shape as items 3–4 but without `subtitle`.

7. **`EventRepository.search_events()`** — same shape as `filter_events()` above.

## Analytics-related

All analytics models are now defined.
