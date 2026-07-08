# Ambient Care — TRMNL Arabic Memory Day-Clock

A gentle, distraction-free ambient information system for an elderly family
member experiencing memory loss. The family sends messages, routine reminders,
and visit reminders from a simple phone app; those appear — in correct
Arabic — on a low-stimulation TRMNL e-paper screen at the elder's home.

```
  Family phones                 Backend (the brain)            Elder's home
  ┌───────────────┐  HTTPS      ┌────────────────────┐  hourly  ┌──────────┐
  │ Flutter PWA   │ ─────────▶  │ FastAPI + SQLite   │  poll    │ TRMNL    │
  │ (login,       │  REST       │  • time/period     │ ◀─────── │ e-paper  │
  │  messages,    │             │  • 800x480 render  │  JSON    │ 800x480  │
  │  schedule)    │ ◀─────────  │  • 24h expiry      │ ───────▶ │ (Arabic) │
  └───────────────┘             └────────────────────┘  html    └──────────┘
```

## What it does

**On the elder's screen** (auto-updating, no interaction needed):
- Giant Arabic time-of-day greeting (صباح الخير / نهارك سعيد / مساء الخير / وقت النوم).
- Weekday + Levantine date (e.g. «الأربعاء • 8 تمّوز 2026»). No clock, no minutes.
- A simple visual checklist of routine tasks for the current period.
- One warm family message (auto-expires after 24h → reassuring fallback).
- Today's 1–2 visits/appointments.
- A rotating famous Arabic Bible verse.
- **Automatic day/night mode**: inverts to black background after 20:00 as a
  strong bedtime cue (helps with sundowning).

**In the family app** (hyper-minimal, one action per screen):
- Shared-passcode login (log in once, stay in).
- Device online/offline status at a glance.
- Send a message — 120-char cap, 5-second double-tap guard.
- Manage routine tasks (check off) and visits.

## Repository layout

```
backend/     FastAPI app — aggregation, time logic, HTML renderer, auth   (see backend/README.md)
frontend/    Flutter PWA — the family dashboard
docs/        DEPLOYMENT.md and TRMNL_INTEGRATION.md
Dockerfile   Single-image build (PWA + API)
render.yaml  One-click Render blueprint
```

## Quick start (local)

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env      # edit AC_FAMILY_PASSCODE + AC_JWT_SECRET
.\.venv\Scripts\python.exe smoke_test.py           # opens preview_day/night.html
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
flutter run -d chrome --dart-define=API_BASE=http://localhost:8000
```

Preview the elder's screen at <http://localhost:8000/api/trmnl.html>.

## Design decisions

| Choice | Why |
|---|---|
| **FastAPI + SQLite** | Lightweight single-file storage, safe concurrency, zero external services. |
| **Shared family passcode (JWT)** | A handful of trusted, non-tech users. No SMS cost, no per-user friction — log in once. |
| **Render, single Docker image** | API + PWA on one HTTPS origin. Firebase can't host the Python server (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)). |
| **Server-rendered HTML fragment** | The device gets pixel-identical output to the browser preview; layout logic lives in one place. |
| **Riverpod** | Predictable, lightweight state for the PWA. |

## Next steps / ideas
- Family photo upload (TRMNL renders `<img>`) with a black-and-white caption.
- Multiple rolling messages instead of one.
- Per-sender attribution if you later switch to named accounts.

See **[docs/TRMNL_INTEGRATION.md](docs/TRMNL_INTEGRATION.md)** to connect the device
and **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** to go live.
