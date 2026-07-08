# Connecting the system to a TRMNL private plugin

This links your deployed backend to the TRMNL e-paper device. Do it once; all
future updates (messages, tasks, layout tweaks) flow over Wi-Fi with **zero**
physical contact with the device.

## Prerequisites
* The backend deployed to a public HTTPS URL (see [DEPLOYMENT.md](DEPLOYMENT.md)),
  e.g. `https://ambient-care.onrender.com`.
* Your `AC_TRMNL_POLL_KEY` value (from the deploy env vars). Optional but
  recommended so only your device can read the screen data.

Your two important URLs:

| Purpose | URL |
|---|---|
| Device data (JSON) | `https://YOUR_HOST/api/trmnl-payload?key=YOUR_POLL_KEY` |
| Browser preview | `https://YOUR_HOST/api/trmnl.html?key=YOUR_POLL_KEY` |

Open the preview URL first in a normal browser — you should see the 800×480
Arabic screen. If that looks right, the device will too.

## Step 1 — Create the private plugin
1. Log in at **usetrmnl.com** → **Plugins** → **Private Plugin** → **New**.
2. **Strategy:** choose **Polling**.
3. **Polling URL:** paste `https://YOUR_HOST/api/trmnl-payload?key=YOUR_POLL_KEY`.
4. **Polling interval:** 60 minutes (the backend caches, so polling is cheap).
5. Save. TRMNL will fetch the URL and show the returned JSON fields, including
   `html`, `period`, `mode`, `weekday`, `date`.

## Step 2 — Set the markup
Open the plugin's **Markup** tab, pick the **Full** layout, and paste exactly:

```liquid
{{ html }}
```

That's it. Our `/api/trmnl-payload` returns a **self-contained fragment** in the
`html` field (scoped `<style>` + one root `<div>`, with the Cairo Arabic font
pulled in via `@import`). Liquid's `{{ html }}` outputs it unescaped, so the
screen renders exactly like the browser preview — day/night mode, RTL, verses
and all.

> The extra JSON fields (`period`, `mode`, `weekday`, `date`) are there if you
> ever want to build a fully native TRMNL Liquid layout instead of using our
> pre-rendered `html`. Not required.

## Step 3 — Add it to the playlist
Add the plugin to your device **Playlist**. To keep the memory clock always on
screen, make it the only (or pinned) item so TRMNL doesn't rotate away from it.

## Step 4 — Verify
* Send a message from the Flutter app.
* Hit the preview URL to confirm the message appears.
* Wait for the next device check-in (or force a refresh from the TRMNL app).

## Notes for reliable memory care
* **Keep it powered.** Plug the device into permanent USB-C power so it can
  check in hourly (or more often) without battery worry.
* **Day/Night is automatic.** At 20:00 Asia/Jerusalem the screen inverts to
  black and shows «وقت النوم» — a strong bedtime cue. No action needed.
* **Messages self-expire** after 24h and fall back to a warm default, so the
  screen never looks broken or shows stale notes.
