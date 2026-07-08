# CLAUDE.md — context for AI assistants working on this repo

Read this first. It captures decisions and state that aren't obvious from the
code alone, so work can continue on any machine.

## What this is
**Ambient Care** — an ambient info system for an elderly, Arabic-speaking family
member with memory loss. Family members send messages / routine tasks / visit
reminders from a Flutter PWA → a FastAPI backend aggregates them and renders an
800×480 **monochrome Arabic** screen that a **TRMNL e-paper device** polls and
displays. Everything shown to the elder and the family is in Arabic (RTL).

## Layout
- `backend/` — FastAPI + SQLite. The brain. See `backend/README.md`.
  - `app/time_context.py` day/period + Arabic date/greeting (Asia/Jerusalem)
  - `app/renderer.py` builds the 800×480 fragment (device) + full doc (preview)
  - `app/aggregator.py` assembles + caches the payload
  - `app/repository.py` data access; `app/bible.py` seed verses only
  - `app/main.py` routes + serves the built PWA at `/`
- `frontend/` — Flutter web PWA (Riverpod). Screens: login, home hub, message,
  schedule (tasks+visits), verses.
- `docs/` — DEPLOYMENT.md, DEPLOYMENT_NOTES.md, TRMNL_INTEGRATION.md
- `Dockerfile` (multi-stage: Flutter build → Python runtime), `render.yaml`

## Locked decisions
- **Auth:** single shared family passcode → JWT (not per-user, not SMS).
- **Timezone:** Asia/Jerusalem. Day mode 06:00–19:59; Night (inverted, «وقت النوم»)
  20:00–05:59. No clock/minutes ever — only the period, for memory care.
- **DB:** SQLite. Messages auto-expire after 24h → warm fallback message.
- **Verses:** stored in DB (seeded from `bible.py`), managed in the app.
  Rotation = seeded-random on `date|period` → changes ~4×/day, stable within a
  period. Picker: `repository.pick_verse(seed)`.
- **Display config via .env:** `AC_DISPLAY_FONT` (Cairo/Tajawal/Almarai/…),
  `AC_DAY_BG` (keep near-white — 1-bit e-ink dithers colors).
- **Renderer emits a self-contained fragment** for TRMNL (used as `{{ html }}`
  in a Full-layout private plugin) and a full HTML doc for `/api/trmnl.html`.

## Deployment state (as of 2026-07)
- Hosted on **Render.com free plan** (Docker Blueprint from `render.yaml`).
  Auto-deploys on push to `main`. Render's GitHub App is installed on the owner's
  account (revoking it breaks auto-deploy).
- Render free **sleeps after 15 min idle** → kept awake by a **UptimeRobot**
  monitor pinging `/api/health` every 5 min. Effectively always-on, $0.
- **No persistent disk on free** — SQLite resets on redeploy/recycle. Accepted.
- `AC_TRMNL_POLL_KEY` gates `/api/trmnl-payload` and `/api/trmnl.html`
  (`?key=...`); Render auto-generated it (`generateValue`). It contains symbols,
  so it must be **URL-encoded** in the query string.
- Next task (not yet done): create the TRMNL private plugin — see
  `docs/TRMNL_INTEGRATION.md`.

## Gotchas
- **Python 3.14 on the dev machine:** old pydantic pins try to compile Rust and
  fail. `requirements.txt` uses floor versions (`pydantic>=2.11`) to get cp314
  wheels. The Docker image uses `python:3.12-slim` where anything works.
- After editing Dart, rebuild `frontend/build/web` (`flutter build web --release`)
  for the single-origin/prod serving; `flutter run` reflects source directly.

## How to run locally
Backend: `cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`
Frontend (dev): `cd frontend && flutter run -d chrome --dart-define=API_BASE=http://localhost:8000`
Offline screen preview: `cd backend && .\.venv\Scripts\python.exe smoke_test.py`
See `quick-start.html` for the full local cheat-sheet.
