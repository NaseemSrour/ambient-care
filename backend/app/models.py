"""Pydantic request/response models (the API contract with the Flutter PWA).

These are deliberately separate from the SQLite storage rows so the wire format
and the storage format can evolve independently.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
# Device / TRMNL status
# ---------------------------------------------------------------------------
class DeviceStatus(BaseModel):
    online: bool
    last_seen: datetime | None
    minutes_since_last_seen: int | None
