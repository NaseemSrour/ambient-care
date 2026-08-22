"""Data access layer — every read/write of family data goes through here.

Timestamps are stored as timezone-aware UTC ISO strings and returned as
datetime objects.

A module-level `data_version` counter is bumped on every write so the payload
aggregator can cheaply tell whether its cached HTML is still valid.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import get_settings
from .database import connect
from .models import Message, MessageCreate

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
