import datetime as dt
from sqlalchemy import (create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from . import config

_is_sqlite = config.DATABASE_URL.startswith("sqlite")
if _is_sqlite:
    engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: transparently reconnects if Render restarts/idles the DB connection
    # pool_recycle: drop connections before the server closes them
    engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=5)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()
now = lambda: dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=now)


class AnalysisSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(200))
    mode = Column(String(20))  # individual | group
    persona = Column(String(40), default="General")
    created_at = Column(DateTime, default=now)
    status = Column(String(20), default="processing")  # processing | done | failed
    progress = Column(Integer, default=0)
    step = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    overall_score = Column(Integer, nullable=True)
    is_mock = Column(Boolean, default=False)
    options = Column(JSON, default=dict)
    transcript = Column(Text, nullable=True)  # only stored if user opts in
    presenters = relationship("PresenterReport", cascade="all, delete-orphan")
    team = relationship("TeamReport", uselist=False, cascade="all, delete-orphan")
    questions = relationship("QAQuestion", cascade="all, delete-orphan")


class PresenterReport(Base):
    __tablename__ = "presenter_reports"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    presenter_name = Column(String(120))
    metrics_json = Column(JSON)
    scores_json = Column(JSON)
    issues_json = Column(JSON)
    suggestions_json = Column(JSON)


class TeamReport(Base):
    __tablename__ = "team_reports"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    balance_json = Column(JSON)
    handoff_json = Column(JSON)
    summary = Column(Text)


class QAQuestion(Base):
    __tablename__ = "qa_questions"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    question = Column(Text)
    related_topic = Column(String(200))
    rationale = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(engine)


def fail_stuck_sessions():
    """Analyses run in a background thread. If the server restarts mid-analysis (Render redeploys,
    free-tier spin-down) those rows would stay 'processing' forever, so mark them failed on boot."""
    with SessionLocal() as db:
        n = (db.query(AnalysisSession).filter(AnalysisSession.status == "processing")
             .update({"status": "failed", "error": "The server restarted during analysis. Please upload again."}))
        db.commit()
        return n
