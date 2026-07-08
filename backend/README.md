# Ambient Care — Backend

The central brain. Aggregates family data (messages, routine tasks, visits),
tracks the time of day in **Asia/Jerusalem**, and renders the 800×480
monochrome Arabic HTML polled by the TRMNL e-paper device.

## Run locally (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env    # then edit .env (set a real passcode + JWT secret)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Then open:

* **Elder screen preview:** http://localhost:8000/api/trmnl.html
* **API docs (Swagger):** http://localhost:8000/docs
* **Health:** http://localhost:8000/api/health

## Quick offline preview (no server)

```powershell
.\.venv\Scripts\python.exe smoke_test.py   # writes preview_day.html / preview_night.html
```

## Configuration

All settings come from environment variables (prefix `AC_`) or a `.env` file.
See [.env.example](.env.example). The important ones:

| Variable | Meaning |
|---|---|
| `AC_FAMILY_PASSCODE` | Shared passcode the family types to log in |
| `AC_JWT_SECRET` | Long random string used to sign login tokens |
| `AC_TIMEZONE` | Defaults to `Asia/Jerusalem` |
| `AC_MESSAGE_TTL_HOURS` | Family messages auto-expire after this (default 24) |
| `AC_TRMNL_POLL_KEY` | Optional secret the device sends as `?key=...` |
| `AC_DEFAULT_MESSAGE` | Warm fallback shown when no fresh message exists |

## API summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | – | Liveness |
| POST | `/api/auth/login` | – | Passcode → token |
| GET | `/api/trmnl-payload` | poll key | JSON for the TRMNL device (`html` + metadata) |
| GET | `/api/trmnl.html` | poll key | Raw HTML preview |
| GET/POST/DELETE | `/api/messages` | token | Family messages |
| GET/POST/PATCH/DELETE | `/api/tasks` | token | Routine checklist |
| GET/POST/DELETE | `/api/events` | token | Visits / appointments |
| GET | `/api/status` | token | Is the device online? |

## Architecture

```
app/
  config.py         settings (.env)
  time_context.py   period + day/night + Arabic date/greeting logic
  bible.py          rotating Arabic verses
  database.py       SQLite schema + connection
  models.py         Pydantic API contract
  repository.py     data access + data_version cache signal
  renderer.py       800x480 monochrome RTL HTML generator
  aggregator.py     builds render context + TTL cache
  auth.py           shared-passcode JWT
  main.py           FastAPI routes + static PWA hosting
```

The rendered HTML is cached and only recomputed when the data changes or the
time period / day-night mode flips, so hourly device polls are answered
instantly.
