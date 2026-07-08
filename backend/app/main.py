"""FastAPI application — the central brain.

Routes
------
Public:
  GET  /api/health                 liveness probe
  POST /api/auth/login             exchange the family passcode for a token
  GET  /api/trmnl-payload          JSON polled by the TRMNL device
  GET  /api/trmnl.html             the raw rendered HTML (browser preview)

Protected (family token required):
  GET/POST/DELETE  /api/messages
  GET/POST/PATCH/DELETE  /api/tasks
  GET/POST/DELETE  /api/events
  GET  /api/status                 is the TRMNL device online?

The built Flutter PWA (frontend/build/web) is served at / when present.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from . import aggregator, repository as repo
from .auth import issue_token, require_auth, verify_passcode
from .config import get_settings
from .database import init_db
from .models import (
    BibleVerse,
    BibleVerseCreate,
    DeviceStatus,
    Event,
    EventCreate,
    LoginRequest,
    Message,
    MessageCreate,
    Task,
    TaskCreate,
    TaskUpdate,
    TokenResponse,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # ensure tables exist before serving any request
    yield


app = FastAPI(title="Ambient Care", version=__version__, lifespan=lifespan)

# Small, private app: allow the PWA to call the API from any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    if not verify_passcode(body.passcode):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="الرمز غير صحيح"
        )
    return issue_token()


def _check_poll_key(key: str | None) -> None:
    configured = get_settings().trmnl_poll_key.strip()
    if configured and (key or "").strip() != configured:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


@app.get("/api/trmnl-payload")
def trmnl_payload(key: str | None = Query(default=None)) -> dict:
    """JSON consumed by the TRMNL polling plugin.

    `html` holds the full self-contained screen; the extra fields are handy
    for debugging inside the TRMNL plugin editor.
    """
    _check_poll_key(key)
    repo.touch_device()  # record that the device is alive
    ctx = aggregator.build_render_context()
    fragment = aggregator.get_display_fragment()
    return {
        "html": fragment,
        "mode": ctx.time.mode.value,
        "period": ctx.time.period.value,
        "weekday": ctx.time.weekday_ar,
        "date": ctx.time.date_ar,
        "message_is_fallback": ctx.message_is_fallback,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/trmnl.html", response_class=HTMLResponse)
def trmnl_html(key: str | None = Query(default=None)) -> HTMLResponse:
    """Raw HTML — open this in a browser to preview the elder's screen."""
    _check_poll_key(key)
    return HTMLResponse(content=aggregator.get_preview_document())


# ---------------------------------------------------------------------------
# Messages (protected)
# ---------------------------------------------------------------------------
@app.get("/api/messages", response_model=list[Message], dependencies=[Depends(require_auth)])
def get_messages() -> list[Message]:
    return repo.list_messages(include_expired=False)


@app.post("/api/messages", response_model=Message, dependencies=[Depends(require_auth)])
def post_message(body: MessageCreate) -> Message:
    return repo.add_message(body)


@app.delete("/api/messages/{message_id}", dependencies=[Depends(require_auth)])
def remove_message(message_id: int) -> dict:
    if not repo.delete_message(message_id):
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Tasks (protected)
# ---------------------------------------------------------------------------
@app.get("/api/tasks", response_model=list[Task], dependencies=[Depends(require_auth)])
def get_tasks() -> list[Task]:
    return repo.list_tasks()


@app.post("/api/tasks", response_model=Task, dependencies=[Depends(require_auth)])
def post_task(body: TaskCreate) -> Task:
    return repo.add_task(body)


@app.patch("/api/tasks/{task_id}", response_model=Task, dependencies=[Depends(require_auth)])
def patch_task(task_id: int, body: TaskUpdate) -> Task:
    task = repo.update_task(task_id, body)
    if task is None:
        raise HTTPException(status_code=404, detail="not found")
    return task


@app.delete("/api/tasks/{task_id}", dependencies=[Depends(require_auth)])
def remove_task(task_id: int) -> dict:
    if not repo.delete_task(task_id):
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Events (protected)
# ---------------------------------------------------------------------------
@app.get("/api/events", response_model=list[Event], dependencies=[Depends(require_auth)])
def get_events() -> list[Event]:
    return repo.list_events()


@app.post("/api/events", response_model=Event, dependencies=[Depends(require_auth)])
def post_event(body: EventCreate) -> Event:
    return repo.add_event(body)


@app.delete("/api/events/{event_id}", dependencies=[Depends(require_auth)])
def remove_event(event_id: int) -> dict:
    if not repo.delete_event(event_id):
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Bible verses (protected)
# ---------------------------------------------------------------------------
@app.get("/api/verses", response_model=list[BibleVerse], dependencies=[Depends(require_auth)])
def get_verses() -> list[BibleVerse]:
    return repo.list_verses()


@app.post("/api/verses", response_model=BibleVerse, dependencies=[Depends(require_auth)])
def post_verse(body: BibleVerseCreate) -> BibleVerse:
    return repo.add_verse(body)


@app.delete("/api/verses/{verse_id}", dependencies=[Depends(require_auth)])
def remove_verse(verse_id: int) -> dict:
    if not repo.delete_verse(verse_id):
        raise HTTPException(status_code=404, detail="not found")
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Device status (protected)
# ---------------------------------------------------------------------------
@app.get("/api/status", response_model=DeviceStatus, dependencies=[Depends(require_auth)])
def device_status() -> DeviceStatus:
    last_seen = repo.device_last_seen()
    if last_seen is None:
        return DeviceStatus(online=False, last_seen=None, minutes_since_last_seen=None)
    minutes = int((datetime.now(timezone.utc) - last_seen).total_seconds() // 60)
    # TRMNL polls hourly; allow a grace window before calling it offline.
    return DeviceStatus(online=minutes <= 90, last_seen=last_seen,
                        minutes_since_last_seen=minutes)


# ---------------------------------------------------------------------------
# Serve the built Flutter PWA (if present) at the site root.
# ---------------------------------------------------------------------------
_pwa_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "build" / "web"
if _pwa_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_pwa_dir), html=True), name="pwa")
