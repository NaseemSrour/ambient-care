# Deployment

## Recommended: Render (single service, Docker)

Both the FastAPI backend and the Flutter PWA ship in **one** container (see the
root [`Dockerfile`](../Dockerfile)) and are served from one HTTPS URL. This is
the simplest thing that works and keeps everything same-origin (no CORS, one
domain to remember for the family).

1. Push this repo to GitHub.
2. Render → **New +** → **Blueprint** → select the repo. It reads
   [`render.yaml`](../render.yaml).
3. Set `AC_FAMILY_PASSCODE` in the dashboard (the shared login code).
   `AC_JWT_SECRET` and `AC_TRMNL_POLL_KEY` are auto-generated.
4. Deploy. You get `https://<name>.onrender.com`.
   * Family dashboard: the root URL.
   * Device data: `/api/trmnl-payload?key=...`
   * Screen preview: `/api/trmnl.html?key=...`

### Free plan + keep-alive (no cost, always-on)

`render.yaml` uses `plan: free`. Free services spin down after ~15 min idle,
which would cold-start the device's poll. Keep it awake with a free uptime
monitor:

1. Create a free account at **uptimerobot.com**.
2. **Add New Monitor** → type **HTTP(s)**.
3. URL: `https://<your-service>.onrender.com/api/health`
4. Monitoring interval: **5 minutes**.

That single ping every 5 min keeps the service from ever sleeping (~730 h/month,
within Render's free 750 h allowance). Note: the free plan has **no persistent
disk**, so SQLite data resets if the instance is redeployed/recycled — fine here
(messages are ephemeral; tasks/verses are quick to re-add). For guaranteed
persistence, use `plan: starter` and add a `disk:` block.

**Railway / Fly.io** work identically — point them at the same `Dockerfile`.

## Is Firebase a good fit here?

**Short answer: not for this shape.** Firebase is excellent for static hosting
and its own realtime/Firestore data model, but it does **not** run a long-lived
Python server. To use Firebase you'd split the stack:

* Flutter PWA on **Firebase Hosting**, and
* FastAPI in a container on **Cloud Run**, and
* wire the two together (extra domain/CORS config, cold-start latency on the
  free tier).

That's strictly more moving parts than the single Render service above, for a
tiny always-on app polled once an hour. So: skip Firebase here. Choose it only
if you later drop the Python backend and rewrite the aggregation as Cloud
Functions + Firestore.

The other sensible option is a **$5 VPS** (Hetzner/DigitalOcean) running the same
Docker image behind Caddy for automatic HTTPS — cheapest long-term, but you
manage the box yourself.

## Local development

Run the two halves separately with hot reload:

```powershell
# Terminal 1 — backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Flutter PWA pointed at the local backend
cd frontend
flutter run -d chrome --dart-define=API_BASE=http://localhost:8000
```

For a production-like single-origin test, build the PWA first
(`flutter build web --release`) and just run the backend — it will serve the
built app at `/`.
