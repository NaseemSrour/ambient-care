"""Pydantic request/response models (the API contract with the Flutter PWA).

These are deliberately separate from the SQLite storage rows so the wire format
and the storage format can evolve independently.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskPeriod(str, Enum):
    """Which time block a routine task belongs to."""

    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    ANYTIME = "anytime"  # always shown regardless of period


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    passcode: str


class TokenResponse(BaseModel):
    token: str
    expires_at: datetime


# ---------------------------------------------------------------------------
# Family messages
# ---------------------------------------------------------------------------
class MessageCreate(BaseModel):
    # 120-char cap mirrors the Flutter field limit so the text always fits the
    # 800x480 screen without breaking the layout.
    text: str = Field(min_length=1, max_length=120)


class Message(BaseModel):
    id: int
    text: str
    created_at: datetime
    expires_at: datetime


# ---------------------------------------------------------------------------
# Routine tasks (visual checklist)
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    period: TaskPeriod = TaskPeriod.ANYTIME


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    period: TaskPeriod | None = None
    done: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    period: TaskPeriod
    done: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Appointments / visits
# ---------------------------------------------------------------------------
class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    # ISO date "2026-07-08"; the day the event happens.
    event_date: str
    # Free-text, human time like "حوالي الساعة ٥ مساءً" — never a strict clock.
    time_text: str = Field(default="", max_length=40)


class Event(BaseModel):
    id: int
    title: str
    event_date: str
    time_text: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Bible verses (family-managed, auto-rotated daily on the display)
# ---------------------------------------------------------------------------
class BibleVerseCreate(BaseModel):
    text: str = Field(min_length=1, max_length=160)
    reference: str = Field(default="", max_length=60)


class BibleVerse(BaseModel):
    id: int
    text: str
    reference: str


# ---------------------------------------------------------------------------
# Device / TRMNL status
# ---------------------------------------------------------------------------
class DeviceStatus(BaseModel):
    online: bool
    last_seen: datetime | None
    minutes_since_last_seen: int | None
