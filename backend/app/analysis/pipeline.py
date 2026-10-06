import shutil
import tempfile
import time
from pathlib import Path
from sqlalchemy.orm import Session
from .. import config
from ..db import SessionLocal, AnalysisSession, PresenterReport, TeamReport, QAQuestion
from . import speech, slides as sl, llm, scoring, mock, stt

STEPS = ["Transcription", "Speaker Diarization", "Visual Pose & Eye Contact", "Slide-to-Speech Sync",
         "LLM Semantic Analysis", "Simulated Q&A Generation"]


def build_team(presenters, spk_seconds, handoffs, slide_speakers):
    total = sum(s["seconds"] for s in spk_seconds) or 1
    balance = [{"name": s["name"], "seconds": round(s["seconds"]), "pct": round(100 * s["seconds"] / total)} for s in spk_seconds]
    gaps = [h["gap"] for h in handoffs]
    interruptions = sum(1 for g in gaps if g < 0)
    avg = sum(abs(g) for g in gaps) / len(gaps) if gaps else 0
    smooth = scoring.clamp(100 - max(0, avg - 1.0) * 12 - interruptions * 6) if gaps else 100
    for h in handoffs:
        h["type"] = "interruption" if h["gap"] < 0 else "handoff"
    ov = [p["scores"]["overall"] for p in presenters]
    spread = (max(ov) - min(ov)) if ov else 0
    cons = "HIGH" if spread <= 10 else "MEDIUM" if spread <= 20 else "LOW"
    top = max(balance, key=lambda b: b["pct"]) if balance else None
    summary = (f"Handoffs were {'smooth' if smooth >= 80 else 'uneven'} (avg gap {round(avg, 1)}s). "
               f"Consistency across presenters is {cons.lower()}. ")
    plan = []
    if top and top["pct"] > 100 / max(1, len(balance)) + 12:
        summary += f"Speaking time leaned toward {top['name']} ({top['pct']}%)."
        plan.append(f"Balance speaking time. {top['name']} could hand over about {top['pct'] - round(100 / len(balance))}% of their time.")
    else:
        summary += "Speaking time was well balanced."
    if interruptions:
        plan.append("Agree on a clear verbal cue for handoffs to avoid talking over each other.")
    if cons != "HIGH":
        plan.append("Rehearse together to align pace, filler habits and slide style.")
    return {"balance": balance, "handoff": {"transitions": handoffs, "smoothness": smooth, "consistency": cons,
                                           "avg_gap": round(avg, 1), "slide_speakers": slide_speakers, "plan": plan},
            "summary": summary}


def _real(media: Path, slides_path, opts, work: Path, step):
    mode, persona = opts["mode"], opts["persona"]
    step(0)
    wav = stt.to_wav(media, work)
    res = stt.transcribe(wav, work, diarize=(mode == "group"), num_speakers=opts.get("num_speakers"),
                         language=opts.get("language"))
    entries = res["entries"]
    step(1)
    if mode == "individual":
        for e in entries:
            e["speaker"] = "0"
    speakers = sorted({e["speaker"] for e in entries}, key=lambda s: (len(s), s))
    names = {s: (opts["name"] if mode == "individual" else f"Speaker {i + 1}") for i, s in enumerate(speakers)}
    pitch = speech.pitch_stats(wav, entries)
    step(2)  # computer vision (MediaPipe) is not part of this build: values stay empty and are shown as "n/a"
    step(3)
    slide_texts = sl.parse_slides(slides_path) if slides_path else []
    q = sl.quality(slide_texts) if slide_texts else None
    aligned = sl.align(entries, slide_texts) if slide_texts else []
    heur = sl.heuristic_coverage(aligned, slide_texts) if slide_texts else []
    step(4)
    full = " ".join(e["text"] for e in entries)
    ai = llm.semantic_analysis(full, slide_texts, persona, opts.get("qa", True)) or {}
    cov = heur
    llm_cov = {c.get("slide"): c for c in ai.get("coverage", []) if isinstance(c, dict)}
    if llm_cov and slide_texts:
        cov = [{**h, **{k: llm_cov[h["slide"]][k] for k in ("status", "note") if k in llm_cov[h["slide"]]}} if h["slide"] in llm_cov else h for h in heur]
    step(5)
    presenters = []
    for s in speakers:
        m = speech.speaker_metrics(entries, s, pitch.get(s))
        if aligned:
            m["slide_time"] = [{"slide": a["slide"], "seconds": round(a["speakers"].get(s, 0))} for a in aligned]
        sc = {"delivery": scoring.delivery_score(m), "coverage": scoring.coverage_score(cov),
              "slides": scoring.slide_score(q), "engagement": scoring.engagement_score(m)}
        sc["overall"] = scoring.overall(sc)
        presenters.append({"name": names[s], "_spk": s, "metrics": m, "scores": sc,
                           "issues": {"coverage": cov, "slide_quality": q, "skipped_topics": ai.get("skipped_topics", [])},
                           "suggestions": scoring.suggestions(m, sc, cov, q)})
    team = None
    if mode == "group" and len(presenters) > 1:
        sec = [{"name": p["name"], "seconds": p["metrics"]["speaking_seconds"]} for p in presenters]
        by = {p["_spk"]: p["name"] for p in presenters}
        hand = [{"from": by[a["speaker"]], "to": by[b["speaker"]], "at": round(b["start"]), "gap": round(b["start"] - a["end"], 1)}
                for a, b in zip(entries, entries[1:]) if a["speaker"] != b["speaker"]]
        ss = [{"slide": a["slide"], "speaker": by[max(a["speakers"], key=a["speakers"].get)]} for a in aligned if a["speakers"]]
        team = build_team(presenters, sec, hand, ss)
        if ai.get("summary"):
            team["summary"] += " " + ai["summary"]
    qa = [{"question": x.get("question", ""), "related_topic": x.get("related_topic", ""), "rationale": x.get("rationale", "")}
          for x in (ai.get("questions") or []) if isinstance(x, dict)][:5]
    if opts.get("qa", True) and not qa:  # LLM unavailable -> simple gap-based questions
        gaps = [c for c in cov if c["status"] != "strong"][:5]
        base = mock.QS.get(persona, mock.QS["General"])
        for i in range(5):
            if i < len(gaps):
                g = gaps[i]
                qa.append({"question": f"Can you go deeper on '{g['title']}'? It felt {g['status'].replace('insufficient', 'under-explained')}.",
                           "related_topic": g["title"], "rationale": g["note"]})
            else:
                qa.append({"question": base[i][0], "related_topic": base[i][1], "rationale": base[i][2]})
    transcript = "\n".join(f"[{names[e['speaker']]} {int(e['start'] // 60):02d}:{int(e['start'] % 60):02d}] {e['text']}" for e in entries) if opts.get("store_transcript") else None
    for p in presenters:
        p.pop("_spk", None)
    return {"presenters": presenters, "team": team, "qa": qa if opts.get("qa", True) else [], "transcript": transcript}


def run(session_id: int, media: Path | None, slides_path: Path | None, opts: dict, workdir: Path):
    db: Session = SessionLocal()
    sess = db.get(AnalysisSession, session_id)

    def step(i):
        sess.step = i
        sess.progress = int(100 * i / len(STEPS))
        db.commit()

    try:
        if config.use_mock():
            sess.is_mock = True
            names = opts["names"]
            for i in range(len(STEPS)):
                step(i)
                time.sleep(1.2)
            result = mock.mock_result(opts["mode"], opts["persona"], names, opts.get("store_transcript"), seed=session_id * 7 + 3)
        else:
            result = _real(media, slides_path, opts, workdir, step)
        for p in result["presenters"]:
            db.add(PresenterReport(session_id=session_id, presenter_name=p["name"], metrics_json=p["metrics"],
                                   scores_json=p["scores"], issues_json=p["issues"], suggestions_json=p["suggestions"]))
        t = result["team"]
        if t:
            db.add(TeamReport(session_id=session_id, balance_json=t["balance"], handoff_json=t["handoff"], summary=t["summary"]))
        for x in result["qa"]:
            db.add(QAQuestion(session_id=session_id, **x))
        sess.transcript = result["transcript"]
        ov = [p["scores"]["overall"] for p in result["presenters"]]
        sess.overall_score = round(sum(ov) / len(ov)) if ov else 0
        sess.progress, sess.step, sess.status = 100, len(STEPS), "done"
        db.commit()
    except Exception as ex:
        db.rollback()
        sess = db.get(AnalysisSession, session_id)
        sess.status, sess.error = "failed", str(ex)[:500]
        db.commit()
    finally:
        db.close()
        shutil.rmtree(workdir, ignore_errors=True)  # PRIVACY: uploads are always deleted
