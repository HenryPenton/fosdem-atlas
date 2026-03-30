"""DuckDB implementation of the IngestionRepository port."""

from __future__ import annotations

import logging

import duckdb
import yake

from src.adapters.persistence.duckdb_connection import DuckDBConnection
from src.domain.models import Event

logger = logging.getLogger(__name__)

_TOPIC_STOPWORDS = {
    # ── HTML / URL artefacts ──────────────────────────────────────────────
    "href",
    "https",
    "strong",
    "'ll",
    "\u2019ll",
    # ── Conference-specific ───────────────────────────────────────────────
    "fosdem",
    "fosdem junior",
    "bof",
    "devroom",
    # ── Presentation / talk language ──────────────────────────────────────
    "talk",
    "talk presents",
    "talk explores",
    "talk introduces",
    "talk covers",
    "talk shares",
    "talk shows",
    "session",
    "presentation",
    "overview",
    "introduction",
    "update",
    "status update",
    "case study",
    "lightning talk",
    "present",
    "explore",
    "share",
    # ── "open source" and all its fragments / variants ────────────────────
    "open",
    "source",
    "open source",
    "open-source",
    "free software",
    "free open",
    "fully open",
    "open software",
    "open-source software",
    "open-source project",
    "open-source projects",
    "open-source tools",
    "source project",
    "source projects",
    "source code",
    "source community",
    "source communities",
    "source tools",
    "source software",
    "source ecosystem",
    "source foundations",
    "foss projects",
    "software projects",
    "software tools",
    "software foundation",
    "android open",
    "linux foundation",
    # ── Generic nouns / verbs too common at any tech conference ────────────
    "software",
    "code",
    "data",
    "tool",
    "tools",
    "project",
    "projects",
    "system",
    "systems",
    "user",
    "users",
    "developer",
    "developers",
    "community",
    "application",
    "applications",
    "feature",
    "features",
    "development",
    "approach",
    "work",
    "build",
    "building",
    "support",
    "make",
    "challenges",
    "platform",
    "platforms",
    "design",
    "model",
    "models",
    "ecosystem",
    "network",
    "framework",
    "infrastructure",
    "service",
    "services",
    "solution",
    "solutions",
    "process",
    "technology",
    "based",
    "time",
    "years",
    "modern",
    "future",
    "public",
    "free",
    "real world",
    "world",
    "digital",
}


class DuckDBIngestionRepository:
    """DuckDB implementation of IngestionRepository — writes events, speakers, and keywords."""

    def __init__(self, connection: DuckDBConnection) -> None:
        self._db = connection

    def insert_events(self, events: list[Event]) -> int:
        with self._db.lock:
            conn = self._db.get()
            conn.execute("BEGIN")
            try:
                conn.execute("DELETE FROM event_speakers")
                conn.execute("DELETE FROM event_links")
                conn.execute("DELETE FROM keywords")
                conn.execute("DELETE FROM events")
                conn.execute("DELETE FROM speakers")
                logger.debug("Cleared existing data, inserting %d events", len(events))

                for event in events:
                    conn.execute(
                        """
                        INSERT INTO events
                            (id, title, subtitle, abstract, start_time,
                             duration_minutes, room, track, day)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            event.id,
                            event.title,
                            event.subtitle,
                            event.abstract,
                            event.start_time,
                            event.duration_minutes,
                            event.room,
                            event.track,
                            event.day,
                        ],
                    )

                    for speaker in event.speakers:
                        conn.execute(
                            "INSERT OR IGNORE INTO speakers (id, name, bio) VALUES (?, ?, ?)",
                            [speaker.id, speaker.name, speaker.bio],
                        )
                        conn.execute(
                            "INSERT OR IGNORE INTO event_speakers (event_id, speaker_id) VALUES (?, ?)",
                            [event.id, speaker.id],
                        )

                    for link in event.links:
                        if link.href:
                            conn.execute(
                                "INSERT OR IGNORE INTO event_links (event_id, href, title) VALUES (?, ?, ?)",
                                [event.id, link.href, link.title],
                            )

                self._extract_keywords(conn, events)
                conn.execute("COMMIT")
                logger.info("Committed %d events to database", len(events))
            except Exception:
                conn.execute("ROLLBACK")
                logger.exception("Event insertion failed, rolled back")
                raise

        return len(events)

    def _extract_keywords(self, conn: duckdb.DuckDBPyConnection, events: list[Event]) -> None:
        if not events:
            return

        full_text = ". ".join(f"{e.title}. {e.abstract}" for e in events)
        extractor = yake.KeywordExtractor(lan="en", n=2, top=120, dedupLim=0.5)
        raw_keywords = extractor.extract_keywords(full_text)

        candidates = [
            kw for kw, _ in raw_keywords if kw.lower() not in _TOPIC_STOPWORDS and len(kw) > 2
        ]

        docs = [f"{e.title} {e.abstract}".lower() for e in events]
        results: list[tuple[str, int]] = []
        for term in candidates:
            count = sum(1 for doc in docs if term.lower() in doc)
            if count >= 2:
                results.append((term, count))

        seen_lower: set[str] = set()
        for term, count in sorted(results, key=lambda x: (-x[1], x[0])):
            low = term.lower()
            if low not in seen_lower:
                seen_lower.add(low)
                conn.execute(
                    "INSERT INTO keywords (term, count) VALUES (?, ?)",
                    [term, count],
                )
