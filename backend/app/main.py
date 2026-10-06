import shutil
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import config
from .auth import get_db, current_user, hash_pw, check_pw, make_token
from .db import init_db, fail_stuck_sessions, User, AnalysisSession, PresenterReport, TeamReport, QAQuestion
from .analysis import pipeline

app = FastAPI(title="AI Presentation Silent Audience")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
init_db()
fail_stuck_sessions()

MEDIA_EXT = {".mp4", ".mp3", ".wav", ".m4a", ".webm", ".mov"}
SLIDE_EXT = {".pptx", ".pdf"}
MAX_BYTES = 500 * 1024 * 1024


class Signup(BaseModel):
    name: str
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


def user_out(u):
    return {"id": u.id, "name": u.name, "email": u.email}


@app.get("/api/health")
def health():
    return {"ok": True, "mock_mode": config.use_mock()}


@app.post("/api/auth/signup")
def signup(b: Signup, db: Session = Depends(get_db)):
    email = b.email.strip().lower()
    if "@" not in email or len(b.password) < 6:
        raise HTTPException(400, "Enter a valid email and a password of at least 6 characters")
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "An account with this email already exists")
    u = User(name=b.name.strip() or "User", email=email, password_hash=hash_pw(b.password))
    db.add(u)
    db.commit()
    return {"token": make_token(u.id), "user": user_out(u)}


@app.post("/api/auth/login")
def login(b: Login, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=b.email.strip().lower()).first()
    if not u or not check_pw(b.password, u.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"token": make_token(u.id), "user": user_out(u)}


@app.get("/api/auth/me")
def me(u: User = Depends(current_user)):
    return user_out(u)


async def _save(up: UploadFile, dest: Path):
    size = 0
    with dest.open("wb") as f:
        while chunk := await up.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                raise HTTPException(413, "File too large (max 500MB)")
            f.write(chunk)


@app.post("/api/sessions")
async def create_session(
    bg: BackgroundTasks,
    mode: str = Form("individual"), persona: str = Form("General"), title: str = Form(""),
    store_transcript: bool = Form(False), enable_cv: bool = Form(True), enable_qa: bool = Form(True),
    num_speakers: Optional[int] = Form(None), language: Optional[str] = Form(None),
    speaker_names: str = Form(""),
    media: Optional[UploadFile] = File(None), slides: Optional[UploadFile] = File(None),
    u: User = Depends(current_user), db: Session = Depends(get_db),
):
    if mode not in ("individual", "group"):
        raise HTTPException(400, "mode must be individual or group")
    mock = config.use_mock()
    if not mock and not media:
        raise HTTPException(400, "Please upload a video or audio file")
    work = Path(tempfile.mkdtemp(prefix="sa_"))  # temp dir, deleted after analysis
    media_path = slides_path = None
    try:
        if media:
            ext = Path(media.filename).suffix.lower()
            if ext not in MEDIA_EXT:
                raise HTTPException(400, "Unsupported media type. Use mp4, mp3 or wav")
            media_path = work / ("media" + ext)
            await _save(media, media_path)
        if slides:
            ext = Path(slides.filename).suffix.lower()
            if ext not in SLIDE_EXT:
                raise HTTPException(400, "Slides must be .pptx or .pdf")
            slides_path = work / ("slides" + ext)
            await _save(slides, slides_path)
    except Exception:
        shutil.rmtree(work, ignore_errors=True)
        raise
    default_title = (media.filename if media else "Sample presentation")
    s = AnalysisSession(user_id=u.id, title=title.strip() or default_title, mode=mode, persona=persona)
    n = max(2, min(6, num_speakers or 3))
    s.options = {"cv": enable_cv, "qa": enable_qa, "store_transcript": store_transcript}
    db.add(s)
    db.commit()
    names = [x.strip() for x in speaker_names.split(",") if x.strip()] if mode == "group" else []
    if mode == "individual":
        names = [u.name]
    elif len(names) < 2:
        names = [f"Speaker {i + 1}" for i in range(n)]
    opts = {"mode": mode, "persona": persona, "qa": enable_qa, "store_transcript": store_transcript,
            "num_speakers": num_speakers, "language": language, "name": u.name, "names": names}
    bg.add_task(pipeline.run, s.id, media_path, slides_path, opts, work)
    return {"id": s.id}


def _own(db, u, sid) -> AnalysisSession:
    s = db.get(AnalysisSession, sid)
    if not s or s.user_id != u.id:
        raise HTTPException(404, "Session not found")
    return s


def brief(s):
    return {"id": s.id, "title": s.title, "mode": s.mode, "persona": s.persona, "status": s.status,
            "overall_score": s.overall_score, "created_at": s.created_at.isoformat(), "is_mock": s.is_mock}


@app.get("/api/sessions")
def list_sessions(u: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(AnalysisSession).filter_by(user_id=u.id).order_by(AnalysisSession.created_at.desc()).all()
    return [brief(s) for s in rows]


@app.get("/api/sessions/{sid}/status")
def status(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _own(db, u, sid)
    return {"id": s.id, "title": s.title, "status": s.status, "progress": s.progress, "step": s.step,
            "steps": pipeline.STEPS, "error": s.error}


@app.get("/api/sessions/{sid}")
def get_session(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _own(db, u, sid)
    d = brief(s)
    d["transcript"] = s.transcript
    d["presenters"] = [{"id": p.id, "name": p.presenter_name, "metrics": p.metrics_json, "scores": p.scores_json,
                        "issues": p.issues_json, "suggestions": p.suggestions_json} for p in s.presenters]
    d["team"] = ({"balance": s.team.balance_json, "handoff": s.team.handoff_json, "summary": s.team.summary}
                 if s.team else None)
    d["questions"] = [{"question": q.question, "related_topic": q.related_topic, "rationale": q.rationale} for q in s.questions]
    return d


class Rename(BaseModel):
    mapping: dict  # {"Speaker 1": "Sarah"}


@app.patch("/api/sessions/{sid}/speakers")
def rename(sid: int, b: Rename, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _own(db, u, sid)
    m = {k: v.strip() for k, v in b.mapping.items() if v and v.strip()}
    for p in s.presenters:
        if p.presenter_name in m:
            p.presenter_name = m[p.presenter_name]
    if s.team:
        bal = [dict(x, name=m.get(x["name"], x["name"])) for x in s.team.balance_json]
        h = dict(s.team.handoff_json)
        h["transitions"] = [dict(t, **{"from": m.get(t["from"], t["from"]), "to": m.get(t["to"], t["to"])}) for t in h["transitions"]]
        h["slide_speakers"] = [dict(x, speaker=m.get(x["speaker"], x["speaker"])) for x in h.get("slide_speakers", [])]
        h["plan"] = [_sub(x, m) for x in h.get("plan", [])]
        s.team.balance_json, s.team.handoff_json, s.team.summary = bal, h, _sub(s.team.summary, m)
    if s.transcript:
        s.transcript = _sub(s.transcript, m)
    db.commit()
    return {"ok": True}


def _sub(text, m):
    for old, new in m.items():
        text = text.replace(old, new)
    return text


@app.delete("/api/sessions/{sid}")
def delete_session(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own(db, u, sid))
    db.commit()
    return {"ok": True}


@app.get("/api/progress")
def progress(u: User = Depends(current_user), db: Session = Depends(get_db)):
    """Individual-mode attempts in order, with deltas vs. the previous attempt."""
    rows = (db.query(AnalysisSession).filter_by(user_id=u.id, mode="individual", status="done")
            .order_by(AnalysisSession.created_at).all())
    out, prev = [], None
    for i, s in enumerate(rows, 1):
        sc = s.presenters[0].scores_json if s.presenters else {}
        m = s.presenters[0].metrics_json if s.presenters else {}
        row = {"attempt": i, "id": s.id, "title": s.title, "created_at": s.created_at.isoformat(), "overall": s.overall_score,
               "delivery": sc.get("delivery"), "coverage": sc.get("coverage"), "slides": sc.get("slides"),
               "engagement": sc.get("engagement"), "wpm": m.get("wpm"), "filler_per_min": m.get("filler_per_min")}
        row["delta"] = ({k: (row[k] - prev[k]) if row[k] is not None and prev[k] is not None else None
                         for k in ("overall", "delivery", "coverage", "slides", "engagement")} if prev else None)
        out.append(row)
        prev = row
    return out


@app.delete("/api/me/data")
def delete_my_data(delete_account: bool = False, u: User = Depends(current_user), db: Session = Depends(get_db)):
    for s in db.query(AnalysisSession).filter_by(user_id=u.id).all():
        db.delete(s)
    if delete_account:
        db.delete(u)
    db.commit()
    return {"ok": True}
