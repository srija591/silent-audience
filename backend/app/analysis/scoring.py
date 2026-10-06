def clamp(x):
    return int(max(0, min(100, round(x))))


def delivery_score(m):
    s = 100.0
    wpm = m["wpm"]
    if wpm < 120:
        s -= (120 - wpm) * 0.8
    elif wpm > 160:
        s -= (wpm - 160) * 0.8
    s -= min(30, max(0, m["filler_per_min"] - 2) * 5)
    s -= min(10, m["repetition_count"] * 0.5)
    s -= min(10, m["longest_pause_s"] * 1.0) if m["longest_pause_s"] > 4 else 0
    if m.get("monotone") == "High":
        s -= 12
    elif m.get("monotone") == "Medium":
        s -= 4
    return clamp(s)


def coverage_score(cov):
    if not cov:
        return None
    w = {"strong": 1, "verbatim": 0.5, "insufficient": 0.5, "skipped": 0}
    return clamp(100 * sum(w.get(c["status"], 0.5) for c in cov) / len(cov))


def slide_score(q):
    if not q or not q["slide_count"]:
        return None
    s = 100 - max(0, q["avg_words_per_slide"] - 50) * 0.5
    s -= max(0, 60 - q["readability"]) * 0.3
    s -= max(0, q["jargon_density_pct"] - 12) * 1.2
    s -= len(q["dense_slides"]) * 3
    return clamp(s)


def engagement_score(m):
    parts = []
    if m.get("eye_contact_pct") is not None:
        parts.append(min(100, m["eye_contact_pct"] * 1.2))
    if m.get("monotone"):
        parts.append({"Low": 90, "Medium": 70, "High": 40}[m["monotone"]])
    if m.get("posture_score") is not None:
        parts.append(m["posture_score"])
    tl = [t["wpm"] for t in m.get("timeline", []) if t["wpm"]]
    if len(tl) >= 3:  # some pace variation = more lively delivery
        mean = sum(tl) / len(tl)
        sd = (sum((x - mean) ** 2 for x in tl) / len(tl)) ** 0.5
        parts.append(60 + min(30, sd / max(mean, 1) * 200))
    return clamp(sum(parts) / len(parts)) if parts else None


def overall(sc):
    w = {"delivery": .35, "coverage": .30, "slides": .20, "engagement": .15}
    tot = sum(w[k] for k in w if sc.get(k) is not None)
    return clamp(sum(sc[k] * w[k] for k in w if sc.get(k) is not None) / tot) if tot else 0


def suggestions(m, sc, cov, q):
    out = []
    if m["wpm"] > 165:
        out.append(f"You spoke at {m['wpm']} WPM. Slow down to 130-160 WPM and pause after key points.")
    elif m["wpm"] < 110:
        out.append(f"At {m['wpm']} WPM the pace is slow. Tighten sentences to keep the audience engaged.")
    if m["filler_per_min"] > 3:
        top = sorted(m["filler_breakdown"].items(), key=lambda x: -x[1])[:2]
        out.append("Reduce filler words (" + ", ".join(f"'{k}' x{v}" for k, v in top) + "). Replace them with a silent pause.")
    if m.get("monotone") == "High":
        out.append("Your pitch varies very little. Emphasise key words and vary your tone to sound more dynamic.")
    if m.get("eye_contact_pct") is not None and m["eye_contact_pct"] < 60:
        out.append("Face the audience more. Try glancing at slides only briefly.")
    skipped = [c for c in cov if c["status"] == "skipped"]
    verb = [c for c in cov if c["status"] == "verbatim"]
    insuff = [c for c in cov if c["status"] == "insufficient"]
    if skipped:
        out.append("Cover skipped slides: " + ", ".join(str(c["slide"]) for c in skipped) + ".")
    if verb:
        out.append("Avoid reading slides verbatim (slides " + ", ".join(str(c["slide"]) for c in verb) + "). Add your own explanation.")
    if insuff:
        out.append("Explain more on slides " + ", ".join(str(c["slide"]) for c in insuff) + ".")
    if q and q["dense_slides"]:
        out.append("Slides " + ", ".join(map(str, q["dense_slides"])) + " are text-heavy. Split them or use visuals.")
    if q and q["jargon_density_pct"] > 15:
        out.append("Jargon density is high. Define technical terms or simplify wording for a broader audience.")
    return out or ["Great job. Keep practising to stay consistent."]
