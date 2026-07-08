"""Data access layer — every read/write of family data goes through here.

Timestamps are stored as timezone-aware UTC ISO strings and returned as
datetime objects. Event dates are plain local calendar dates ("YYYY-MM-DD").

A module-level `data_version` counter is bumped on every write so the payload
aggregator can cheaply tell whether its cached HTML is still valid.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from .bible import Verse
from .config import get_settings
from .database import connect
from .models import (
    BibleVerse,
    BibleVerseCreate,
    Event,
    EventCreate,
    Message,
    MessageCreate,
    Task,
    TaskCreate,
    TaskPeriod,
    TaskUpdate,
)

# Bumped on every mutation; read by the aggregator's cache.
data_version: int = 0


def _bump() -> None:
    global data_version
    data_version += 1


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
def add_message(payload: MessageCreate) -> Message:
    now = _now_utc()
    expires = now + timedelta(hours=get_settings().message_ttl_hours)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO messages (text, created_at, expires_at) VALUES (?, ?, ?)",
            (payload.text.strip(), _iso(now), _iso(expires)),
        )
        message_id = cur.lastrowid
    _bump()
    return Message(id=message_id, text=payload.text.strip(),
                   created_at=now, expires_at=expires)


def list_messages(*, include_expired: bool = False) -> list[Message]:
    query = "SELECT * FROM messages"
    params: tuple = ()
    if not include_expired:
        query += " WHERE expires_at > ?"
        params = (_iso(_now_utc()),)
    query += " ORDER BY created_at DESC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [
        Message(id=r["id"], text=r["text"],
                created_at=_parse(r["created_at"]),
                expires_at=_parse(r["expires_at"]))
        for r in rows
    ]


def latest_message() -> Message | None:
    """Most recent non-expired message, or None (renderer shows fallback)."""
    messages = list_messages(include_expired=False)
    return messages[0] if messages else None


def delete_message(message_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        deleted = cur.rowcount > 0
    if deleted:
        _bump()
    return deleted


def purge_expired_messages() -> int:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM messages WHERE expires_at <= ?", (_iso(_now_utc()),)
        )
        removed = cur.rowcount
    if removed:
        _bump()
    return removed


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
def _row_to_task(r) -> Task:
    return Task(id=r["id"], title=r["title"], period=TaskPeriod(r["period"]),
                done=bool(r["done"]), created_at=_parse(r["created_at"]))


def add_task(payload: TaskCreate) -> Task:
    now = _now_utc()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, period, done, created_at) VALUES (?, ?, 0, ?)",
            (payload.title.strip(), payload.period.value, _iso(now)),
        )
        task_id = cur.lastrowid
    _bump()
    return Task(id=task_id, title=payload.title.strip(),
                period=payload.period, done=False, created_at=now)


def list_tasks() -> list[Task]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at ASC"
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def tasks_for_period(period: TaskPeriod) -> list[Task]:
    """Tasks for the given period plus always-on 'anytime' tasks."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE period IN (?, 'anytime') ORDER BY created_at ASC",
            (period.value,),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def update_task(task_id: int, payload: TaskUpdate) -> Task | None:
    sets, params = [], []
    if payload.title is not None:
        sets.append("title = ?")
        params.append(payload.title.strip())
    if payload.period is not None:
        sets.append("period = ?")
        params.append(payload.period.value)
    if payload.done is not None:
        sets.append("done = ?")
        params.append(1 if payload.done else 0)
    if not sets:
        return get_task(task_id)
    params.append(task_id)
    with connect() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", params)
    _bump()
    return get_task(task_id)


def get_task(task_id: int) -> Task | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def delete_task(task_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        deleted = cur.rowcount > 0
    if deleted:
        _bump()
    return deleted


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
def _row_to_event(r) -> Event:
    return Event(id=r["id"], title=r["title"], event_date=r["event_date"],
                 time_text=r["time_text"], created_at=_parse(r["created_at"]))


def add_event(payload: EventCreate) -> Event:
    now = _now_utc()
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO events (title, event_date, time_text, created_at) "
            "VALUES (?, ?, ?, ?)",
            (payload.title.strip(), payload.event_date,
             payload.time_text.strip(), _iso(now)),
        )
        event_id = cur.lastrowid
    _bump()
    return Event(id=event_id, title=payload.title.strip(),
                 event_date=payload.event_date,
                 time_text=payload.time_text.strip(), created_at=now)


def list_events() -> list[Event]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY event_date ASC, created_at ASC"
        ).fetchall()
    return [_row_to_event(r) for r in rows]


def events_on(local_date: str, *, limit: int = 2) -> list[Event]:
    """Events happening on a specific local calendar date (e.g. today)."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE event_date = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (local_date, limit),
        ).fetchall()
    return [_row_to_event(r) for r in rows]


def delete_event(event_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        deleted = cur.rowcount > 0
    if deleted:
        _bump()
    return deleted


def purge_past_events(before_local_date: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM events WHERE event_date < ?", (before_local_date,)
        )
        removed = cur.rowcount
    if removed:
        _bump()
    return removed


# ---------------------------------------------------------------------------
# Bible verses
# ---------------------------------------------------------------------------
def list_verses() -> list[BibleVerse]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM verses ORDER BY id ASC").fetchall()
    return [
        BibleVerse(id=r["id"], text=r["text"], reference=r["reference"])
        for r in rows
    ]


def add_verse(payload: BibleVerseCreate) -> BibleVerse:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO verses (text, reference, created_at) VALUES (?, ?, ?)",
            (payload.text.strip(), payload.reference.strip(), _iso(_now_utc())),
        )
        verse_id = cur.lastrowid
    _bump()
    return BibleVerse(id=verse_id, text=payload.text.strip(),
                      reference=payload.reference.strip())


def delete_verse(verse_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM verses WHERE id = ?", (verse_id,))
        deleted = cur.rowcount > 0
    if deleted:
        _bump()
    return deleted


def pick_verse(seed: str) -> Verse | None:
    """Pick one verse pseudo-randomly for the given seed.

    The aggregator seeds this with `date|period`, so the verse looks randomly
    chosen yet stays constant across the device's hourly polls within a time
    period, changing ~4x/day at each period boundary. Deterministic across
    restarts (random.Random hashes the string seed reproducibly).
    Returns None only if the family has deleted every verse.
    """
    verses = list_verses()
    if not verses:
        return None
    chosen = random.Random(seed).choice(verses)
    return Verse(text=chosen.text, reference=chosen.reference)


# ---------------------------------------------------------------------------
# Device state (TRMNL last-seen tracking)
# ---------------------------------------------------------------------------
def touch_device() -> None:
    """Record that the TRMNL device just polled us."""
    with connect() as conn:
        conn.execute(
            "UPDATE device_state SET last_seen = ? WHERE id = 1",
            (_iso(_now_utc()),),
        )


def device_last_seen() -> datetime | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT last_seen FROM device_state WHERE id = 1"
        ).fetchone()
    return _parse(row["last_seen"]) if row and row["last_seen"] else None
