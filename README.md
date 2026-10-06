# AI Presentation Silent Audience

A virtual audience that gives objective feedback on recorded presentations.
**Frontend:** React + Tailwind + Recharts (styled after your FlutterFlow design). **Backend:** Python FastAPI + SQLAlchemy (SQLite, PostgreSQL optional). **Speech-to-text + speaker diarization:** Sarvam AI Batch API. **Auth:** JWT + bcrypt.

## Quick start (Windows)
Prerequisites: **Python 3.10+** and **Node.js 18+** (tick "Add Python to PATH" when installing Python).

1. Unzip this folder.
2. Double-click `setup.bat` (installs everything, creates `backend\.env`).
3. Double-click `run-backend.bat` (API on http://localhost:8000, docs at /docs).
4. Double-click `run-frontend.bat`, then open **http://localhost:5173**.

macOS/Linux: run `./setup.sh`, then the two commands it prints.

## Demo mode vs real analysis
With an empty `SARVAM_API_KEY` the app runs in **demo mode**: the whole flow works and reports use realistic **sample data** (marked "sample data"). Good as a hackathon fallback.

For **real analysis**, edit `backend\.env`:
```
SARVAM_API_KEY=your_key_from_dashboard.sarvam.ai
MOCK_MODE=auto        # or false to force real mode
SARVAM_LANGUAGE=en-IN
```
Restart the backend. Pipeline in real mode:
1. ffmpeg (bundled via `imageio-ffmpeg`) extracts 16 kHz mono audio from your video.
2. Sarvam **Batch STT** (`saaras:v4`, `verbatim` mode so "um/uh" are kept) with **diarization** and timestamps. Group mode splits speakers by diarization; rename them on the team report.
3. Local metrics: WPM, filler words, pauses, repetition, speaking time, per-minute timeline, pitch/monotone (if `librosa` is installed).
4. Slides (`.pptx`/`.pdf`): text density, readability, jargon density, slide-to-speech alignment, time per slide.
5. LLM (Sarvam chat by default, configurable in `.env`) for coverage (skipped / insufficient / verbatim), summary and 5 persona-based questions. If the LLM call fails, heuristics are used.
6. Scores: Delivery, Content Coverage, Slide Quality, Engagement, Overall.

## Privacy
Uploads go to a temp folder and are **deleted in a `finally` block** after analysis. Only metrics, scores, issues, suggestions, timeline and Q&A are stored. Transcripts are stored only if the user opts in. **Settings -> Delete my data** removes everything (or the whole account).

## What is and isn't included
| Feature | Status |
|---|---|
| Auth, dashboard, individual + group modes, upload, progress screen | Done |
| Speech metrics, Sarvam STT + diarization, slide analysis, Q&A, scoring | Done (needs `SARVAM_API_KEY` for real data) |
| Group report: balance chart, handoffs, consistency, speaker renaming | Done |
| Progress comparison across attempts, PDF export (browser "Save as PDF") | Done |
| **Eye contact / posture (MediaPipe)** | **Not implemented.** Shows "n/a" in real mode, sample values in demo mode. |
| Pitch/monotone | Needs optional `librosa` |

The Sarvam and LLM calls follow Sarvam's published docs but were not run against the live API in this build. Try one short real file first and read the backend console if something fails.

## Layout
```
backend/app   main.py (routes) db.py auth.py config.py analysis/{stt,speech,slides,llm,scoring,mock,pipeline}.py
frontend/src  App.jsx api.js ui.jsx pages/*.jsx
```
## Deploying on Render (PostgreSQL)
Locally the app uses a SQLite file. In production it uses PostgreSQL: just set `DATABASE_URL`
(Render's `postgres://...` / `postgresql://...` URLs are converted automatically). Tables are created on startup.

1. Push this folder to GitHub (`.env` is git-ignored; never commit API keys).
2. Render dashboard -> **New -> Blueprint** -> select the repo. `render.yaml` creates the Postgres DB, the API and the static frontend.
3. When prompted, fill in `SARVAM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`.
4. After first deploy, set two values and redeploy both services:
   - API service: `CORS_ORIGINS` = your frontend URL (e.g. `https://silent-audience.onrender.com`)
   - Frontend: `VITE_API_URL` = your API URL (e.g. `https://silent-audience-api.onrender.com`)

Notes: free Render Postgres **expires after 30 days** (use a paid plan, or Neon/Supabase and paste their URL into `DATABASE_URL`).
Free web services sleep after inactivity and have 512 MB RAM, so long videos may fail; analyses interrupted by a restart are marked *failed*.
