# Caching Opportunities

This document catalogues the logical places to add in-process LRU caching to
FOSDEM Explorer, ordered roughly by expected impact.

All data returned by the service and repository layers is **scrape-time
static** — it doesn't change between scrapes (~every 5 minutes). This makes
the entire read path a good candidate for short-lived caching.

---

## Important caveat: instance methods and `lru_cache`

`functools.lru_cache` works on plain functions and `@staticmethod` out of the
box, but **not** directly on instance methods (the `self` argument is included
in the cache key, which defeats the purpose and leaks memory).

Three clean options, in order of preference for this codebase:

1. **Cache at the repository layer** — repository methods receive only
   primitive arguments (`str`, `list[str]`), so a module-level helper with
   `@lru_cache` or a `_cache: dict` on the repository instance works well.
2. **Use `@functools.cached_property`** for zero-argument service calls
   (`get_overview`, `get_all_tracks_with_counts`, etc.) — evaluated once per
   instance lifetime and then stored on the instance.
3. **Wrap in a module-level function** that accepts the repository/service as
   an argument — can then be decorated with `@lru_cache`.

The cache should be **invalidated on every scrape** (call `cache_clear()` or
replace the instance). `AnalyticsService` already demonstrates this pattern
with its `invalidate_cache()` method.

---

## Phase A — Highest impact, zero-argument calls (do first)

These methods take no arguments and return the same result until the next
scrape. A `@cached_property` or `lru_cache(maxsize=1)` would turn every
subsequent hit into a dictionary lookup.

| Layer | Method | Why it's expensive |
|-------|--------|--------------------|
| `ScheduleService` | `get_overview()` | Calls `get_events_by_day()` in a loop for every day, plus `get_unique_*` queries |
| `ScheduleService` | `get_all_tracks_with_counts()` | Loops over all tracks counting events per track |
| `SpeakerService` | `get_all_speakers()` | JOIN + GROUP BY across all speakers — drives `/speakers`, the speakers API, and both CSV exports |

---

## Phase B — Small-key-space calls (do second)

These methods accept one argument whose value set is tiny (FOSDEM has 2–3
days; a handful of rooms). `lru_cache(maxsize=8)` covers the full keyspace.

| Layer | Method | Key space |
|-------|--------|-----------|
| `ScheduleService` | `get_grid_data(day)` | ~3 day values; most expensive computation in the app (rowspan/track-change grid built in Python) |
| `ScheduleService` | `get_day_detail(day)` | ~3 day values |
| Repository | `get_unique_days()` | No args — called repeatedly on every page load |
| Repository | `get_unique_tracks()` | No args |
| Repository | `get_unique_rooms()` | No args |

---

## Phase C — Bounded per-item caches (optional, do last)

These methods are keyed by an entity ID. The key space is larger (100s of
events, 100s of speakers) but access patterns are likely Zipf-distributed
(most users look at the same popular talks). A bounded `lru_cache(maxsize=256)`
would serve the hot tail cheaply.

| Layer | Method | Notes |
|-------|--------|-------|
| `ScheduleService` | `get_event_detail(event_id)` | Single event lookup + speaker JOIN |
| `SpeakerService` | `get_speaker_detail(speaker_id)` | Single speaker lookup + event JOIN |

---

## What NOT to cache

| Method | Reason |
|--------|--------|
| `search_events(q, track, room, day)` | Unbounded key space (arbitrary user queries); results already capped at 200 by the DB query |
| `analytics_service.get_analytics()` | Already has a hand-rolled in-memory cache with `invalidate_cache()` tied to the scrape cycle — adding `lru_cache` on top would break that invalidation |
| `build_ical(event_ids)` | Called very infrequently; key is a variable-length list (unhashable without conversion) |
