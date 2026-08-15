# Ankush OSINT Toolkit

**A FastAPI + HTML/CSS/JavaScript OSINT dashboard** for investigating public, open-source
information — usernames, emails, IPs, domains, and image metadata — with a local,
searchable investigation history.

> Use only with public or authorized information. Username "found" results are a
> signal from an HTTP status code, not a confirmed identity match. IP geolocation is
> approximate and is **not** live GPS.

---

## Features

| Tool | What it does |
|---|---|
| **Username Intelligence** | Checks a username against 15+ public platforms (GitHub, Reddit, X, Stack Overflow, Twitch, YouTube, etc.) **concurrently**, and reports response time per platform |
| **Email Intelligence** | Validates format, resolves MX records, flags disposable domains and plus-addressing |
| **IP Intelligence** | Approximate public geolocation, ISP, ASN, and organization for an IPv4/IPv6 address |
| **Domain / DNS Intelligence** | A, MX, NS, TXT records, plus SPF and DMARC posture checks |
| **Image OSINT** | Extracts EXIF metadata, flags GPS presence, generates a SHA-256 fingerprint |
| **History** | Every lookup is logged locally to SQLite — filterable, deletable, and exportable to CSV/JSON |

## Tech stack

- **Backend:** FastAPI, `httpx` (async concurrent requests), `dnspython`, `Pillow`, SQLite
- **Frontend:** Vanilla HTML/CSS/JS — no build step, no framework, no external JS dependencies

## Getting started

### Prerequisites
- Python 3.9+

### Installation

```bash
git clone https://github.com/BOT9315/Ankush-osint-toolkit.git
cd Ankush-osint-toolkit

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r backend/requirements.txt
```

### Run

```bash
cd backend
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000** in your browser.

## Project structure

```
Ankush-osint-toolkit/
├── backend/
│   ├── main.py            # FastAPI app + routes
│   ├── osint.py            # Lookup logic (username, email, IP, domain, image)
│   ├── database.py         # SQLite history storage
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── uploads/                 # Uploaded images for EXIF analysis (gitignored)
├── reports/                  # Reserved for future report exports
└── README.md
```

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/api/health` | Service status |
| `POST` | `/api/username` | `{ "target": "username" }` → cross-platform check |
| `POST` | `/api/email` | `{ "target": "name@domain.com" }` → format/MX/disposable check |
| `POST` | `/api/ip` | `{ "target": "8.8.8.8" }` → geolocation + network info |
| `POST` | `/api/domain` | `{ "target": "example.com" }` → DNS records + SPF/DMARC |
| `POST` | `/api/image` | multipart file upload → EXIF metadata + SHA-256 |
| `GET`  | `/api/history?limit=&offset=&tool=` | Paginated, filterable history |
| `DELETE` | `/api/history/{id}` | Delete a single entry |
| `DELETE` | `/api/history` | Clear all history |
| `GET`  | `/api/history/export?format=json\|csv` | Export history |
| `GET`  | `/api/stats` | Investigation counts by tool |

Interactive docs are also available at `/docs` (Swagger UI) once the server is running.

## Disclaimer

This tool only queries **publicly accessible** information — public profile URLs, DNS
records, public IP geolocation databases, and metadata embedded in files you upload
yourself. It performs no authentication bypass, scraping of private data, or
unauthorized access of any kind. You are responsible for using it in accordance with
the terms of service of any platform you check and the laws of your jurisdiction.

## License

Add your preferred license here (e.g. MIT) — none specified yet.
