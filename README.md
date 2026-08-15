<<<<<<< HEAD
# Ankush OSINT Toolkit 2.1

A FastAPI + HTML/CSS/JavaScript OSINT dashboard for looking up **public, open-source
information** — usernames, email deliverability, IP network data, DNS records, and
image metadata — with a local investigation history.

## What's new in 2.1

**Backend**
- Username checks now run **concurrently** with `httpx.AsyncClient` + `asyncio.gather`
  instead of one-at-a-time requests — checking all platforms is dramatically faster.
- Platform list expanded (Stack Overflow, Hacker News, Keybase, Product Hunt, npm,
  Twitch, Telegram, YouTube) and each result now reports response time.
- Email check reports `has_mx` and flags plus-addressing.
- Domain check adds **SPF / DMARC** posture flags.
- Image metadata flags whether **GPS EXIF data** is present without exposing raw
  coordinates by default in the summary row.
- History endpoint supports pagination + filtering by tool; new endpoints to
  **delete a single entry**, **clear all history**, and **export to CSV/JSON**.

**Frontend**
- Full visual redesign — a "case file" aesthetic: monospace data typography,
  stamped MATCH / NO MATCH badges on results, and a redaction-bar loading animation.
- Working **light / dark theme toggle** (persisted locally).
- Live API status indicator, animated per-tool activity chart on the dashboard.
- Drag-and-drop image upload, one-click copy on any result field.
- History page: filter by tool, delete individual entries, clear all, export
  CSV/JSON.
- Fully responsive down to mobile.

## Features
- Public username profile checks (parallel, 15 platforms)
- Email format / domain / MX / disposable-domain checks
- Public IP intelligence (geolocation is approximate, not live GPS)
- Domain / DNS records including SPF & DMARC
- Image EXIF metadata and SHA-256 hash
- SQLite investigation history with filtering, deletion, and export
- Responsive, theme-able dashboard

## Run locally

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Notes

Use only with public or authorized information. Username "found" results are a
signal from an HTTP status code, not a confirmed identity match. IP geolocation
is approximate and is not live GPS.
=======

>>>>>>> 797f14221e55c94303a403f3fea31142dde606ad
