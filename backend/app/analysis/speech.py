import re
from collections import Counter

FILLERS = ["um", "uh", "uhm", "umm", "erm", "hmm", "like", "you know", "i mean", "basically", "actually"]
_FILLER_RE = {f: re.compile(r"\b" + re.escape(f) + r"\b", re.I) for f in FILLERS}
WORD_RE = re.compile(r"[\w'’-]+", re.UNICODE)


def words(text):
    return WORD_RE.findall(text.lower())


def count_fillers(text):
    c = Counter()
    for f, rx in _FILLER_RE.items():
        n = len(rx.findall(text))
        if n:
            c[f] = n
    return c


def pitch_stats(wav_path, entries):
    """Pitch variation per speaker (std in semitones + Hz). Needs librosa; returns {} if unavailable."""
    try:
        import numpy as np
        import librosa
    except Exception:
        return {}
    try:
        y, sr = librosa.load(str(wav_path), sr=16000, mono=True)
        hop = 320
        f0 = librosa.yin(y, fmin=70, fmax=400, sr=sr, frame_length=1024, hop_length=hop)
        rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0][: len(f0)]
        voiced = rms > (np.median(rms) * 0.8)
        out = {}
        for spk in {e["speaker"] for e in entries}:
            vals = []
            for e in entries:
                if e["speaker"] != spk:
                    continue
                a, b = int(e["start"] * sr / hop), int(e["end"] * sr / hop)
                seg = f0[a:b][voiced[a:b]] if b > a else []
                vals.extend(list(seg))
            if len(vals) > 50:
                v = np.array(vals)
                st = 12 * np.log2(v / np.median(v))
                out[spk] = {"std_hz": round(float(v.std()), 1), "std_semitones": round(float(st.std()), 2)}
        return out
    except Exception:
        return {}


def speaker_metrics(entries, spk, pitch=None):
    mine = [e for e in entries if e["speaker"] == spk]
    text = " ".join(e["text"] for e in mine)
    w = words(text)
    speaking = sum(max(0.0, e["end"] - e["start"]) for e in mine) or 1.0
    fill = count_fillers(text)
    total_fill = sum(fill.values())
    # pauses: gaps >= 0.8s between consecutive chunks of this speaker
    gaps = [b["start"] - a["end"] for a, b in zip(mine, mine[1:]) if 0.8 <= b["start"] - a["end"] <= 15]
    # repetition: immediate duplicate words + repeated trigrams
    dup = sum(1 for a, b in zip(w, w[1:]) if a == b and len(a) > 2)
    tri = Counter(zip(w, w[1:], w[2:]))
    rep_phr = sum(c - 1 for c in tri.values() if c > 1)
    # timeline per minute
    tl = {}
    for e in mine:
        m = int(e["start"] // 60)
        b = tl.setdefault(m, {"minute": m, "fillers": 0, "words": 0, "secs": 0.0})
        b["fillers"] += sum(count_fillers(e["text"]).values())
        b["words"] += len(words(e["text"]))
        b["secs"] += max(0.0, e["end"] - e["start"])
    timeline = [{"minute": b["minute"], "fillers": b["fillers"],
                 "wpm": round(b["words"] / b["secs"] * 60) if b["secs"] > 1 else 0} for _, b in sorted(tl.items())]
    p = pitch or {}
    st = p.get("std_semitones")
    return {
        "word_count": len(w), "speaking_seconds": round(speaking, 1),
        "wpm": round(len(w) / speaking * 60),
        "filler_total": total_fill, "filler_per_min": round(total_fill / (speaking / 60), 1),
        "filler_breakdown": dict(fill),
        "pause_count": len(gaps), "avg_pause_s": round(sum(gaps) / len(gaps), 1) if gaps else 0,
        "longest_pause_s": round(max(gaps), 1) if gaps else 0,
        "repetition_count": dup + rep_phr,
        "pitch_std_hz": p.get("std_hz"),
        "monotone": None if st is None else ("High" if st < 1.8 else "Medium" if st < 2.8 else "Low"),
        "timeline": timeline,
        "eye_contact_pct": None, "posture_score": None, "hand_movement": None,
    }
