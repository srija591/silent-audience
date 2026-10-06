#!/usr/bin/env bash
set -e
cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
pip install -r requirements-optional.txt || true
[ -f .env ] || cp .env.example .env
cd ../frontend && npm install
echo "Done. Run: (cd backend && . venv/bin/activate && uvicorn app.main:app --reload)  and  (cd frontend && npm run dev)"
