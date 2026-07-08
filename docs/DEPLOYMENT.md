# Deployment — options & reasoning

> For the concrete, step-by-step record of how *this* project was actually
> deployed (Render + UptimeRobot + poll key + how to redeploy), see
> **[DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md)**. This file covers the *why* and
> the alternatives.

## Chosen setup
Backend + Flutter PWA ship in **one** Docker image (root [`Dockerfile`](../Dockerfile))
served from a single HTTPS origin (no CORS, one URL for the family), hosted on
**Render.com free plan** via the [`render.yaml`](../render.yaml) Blueprint, kept
always-on with a free **UptimeRobot** ping to `/api/health` every 5 min.

## Is Firebase a good fit here?

**Short answer: not for this shape.** Firebase is great for static hosting and
its own Firestore data model, but it does **not** run a long-lived Python
server. Using it would mean splitting the stack: Flutter PWA on Firebase
Hosting + FastAPI in a container on Cloud Run, wired together (extra CORS/domain
config, cold starts on the free tier). That's more moving parts than one Render
service for a tiny app. Choose Firebase only if you later drop the Python
backend and rewrite the aggregation as Cloud Functions + Firestore.

## Other hosting options
* **Oracle Cloud "Always Free"** — a genuinely free, always-on VM with a real
  disk (data persists). Run the same Docker image behind Caddy or a Cloudflare
  Tunnel for HTTPS. Best free option if you want persistence; ~20–30 min setup.
* **$5 VPS** (Hetzner/DigitalOcean) — same Docker image behind Caddy. Cheapest
  paid, fully yours.
* **Railway / Fly.io / Koyeb** — all take the same `Dockerfile`; free tiers vary
  and change often (Fly dropped its free tier; Koyeb free sleeps after ~1h idle).
* Want persistence on a free managed host? Move storage from local SQLite to a
  free hosted SQLite (**Turso**) — small code change, survives redeploys.

## Local development
See **[../quick-start.html](../quick-start.html)** for the full local run
cheat-sheet (backend + Flutter, single-origin mode, offline preview).
