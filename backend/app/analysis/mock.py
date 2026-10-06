"""Sample data so the whole app works without any API keys."""
import random

QS = {
    "Investor": [("How do you plan to defend your margins if a larger competitor enters next quarter?", "Market Strategy", "Competitive analysis lacked barrier-to-entry data."),
                 ("Your CAC projections look optimistic. What is the fallback if acquisition costs double?", "Financials", "CAC was mentioned but not stress-tested."),
                 ("How much technical debt are you taking on to hit this timeline?", "Technical Debt", "The rollout plan ignored maintenance overhead."),
                 ("At what volume does your cost structure support the margin target?", "Unit Economics", "Revenue curve shown without the cost inflection point."),
                 ("Who on the team can lead the move from R&D to enterprise sales?", "Team", "Organisational roadmap was skipped.")],
    "Professor": [("What is the evidence that your method generalises beyond this dataset?", "Methodology", "Only one dataset was discussed."),
                  ("How did you control for confounding variables?", "Experiment Design", "Controls were not explained."),
                  ("What are the main limitations of this approach?", "Limitations", "Limitations slide was read verbatim."),
                  ("How does this compare with the strongest baseline in the literature?", "Related Work", "Comparison was brief."),
                  ("What would falsify your hypothesis?", "Hypothesis", "Hypothesis was stated but not tested.")],
    "Beginner": [("Can you explain the main idea again without technical terms?", "Core Concept", "Jargon density was high."),
                 ("Why does this problem matter in everyday life?", "Motivation", "Motivation was brief."),
                 ("What does the term on slide 4 mean?", "Terminology", "Term used without definition."),
                 ("Can you give a real-world example?", "Examples", "Few concrete examples."),
                 ("What should I remember as the one key takeaway?", "Summary", "No clear closing summary.")],
}
QS["General"] = QS["Investor"][:2] + QS["Beginner"][:2] + QS["Professor"][:1]


def _presenter(name, rnd, slides=True):
    wpm = rnd.randint(118, 172)
    fill = rnd.randint(4, 22)
    mins = rnd.randint(6, 10)
    timeline = [{"minute": i, "fillers": max(0, int(rnd.gauss(fill / mins, 1.2))), "wpm": wpm + rnd.randint(-18, 18)} for i in range(mins)]
    fb = {"um": fill // 3, "uh": fill // 4, "like": fill // 3, "you know": max(0, fill - fill // 3 - fill // 4 - fill // 3)}
    m = {"word_count": wpm * mins, "speaking_seconds": mins * 60, "wpm": wpm, "filler_total": fill,
         "filler_per_min": round(fill / mins, 1), "filler_breakdown": fb, "pause_count": rnd.randint(8, 25),
         "avg_pause_s": round(rnd.uniform(1.0, 2.2), 1), "longest_pause_s": round(rnd.uniform(2.5, 6), 1),
         "repetition_count": rnd.randint(2, 10), "pitch_std_hz": round(rnd.uniform(14, 40), 1),
         "monotone": rnd.choice(["Low", "Low", "Medium", "High"]), "timeline": timeline,
         "eye_contact_pct": rnd.randint(48, 86), "posture_score": rnd.randint(60, 92), "hand_movement": rnd.choice(["Natural", "Low", "Excessive"])}
    n = 8
    m["slide_time"] = [{"slide": i + 1, "seconds": rnd.randint(20, 110)} for i in range(n)]
    cov = [{"slide": i + 1, "title": t, "status": rnd.choice(["strong", "strong", "insufficient", "verbatim", "skipped"]), "note": ""}
           for i, t in enumerate(["Problem", "Market", "Solution", "Technical Specs", "Traction", "Business Model", "Roadmap", "Risk Mitigation"])]
    for c in cov:
        c["note"] = {"strong": "Strong coverage with good alignment to slide text.", "insufficient": "Insufficiently explained. Transcript lacks depth.",
                     "verbatim": "Read verbatim. High jargon density detected.", "skipped": "Barely discussed in the talk."}[c["status"]]
    q = {"slide_count": n, "avg_words_per_slide": rnd.randint(35, 95), "readability": rnd.randint(38, 72),
         "jargon_density_pct": round(rnd.uniform(6, 22), 1), "dense_slides": [4, 8][: rnd.randint(0, 2)]}
    return m, cov, q


def mock_result(mode, persona, names, store_transcript, seed):
    from .scoring import delivery_score, coverage_score, slide_score, engagement_score, overall, suggestions
    rnd = random.Random(seed)
    presenters = []
    for n in names:
        m, cov, q = _presenter(n, rnd)
        sc = {"delivery": delivery_score(m), "coverage": coverage_score(cov), "slides": slide_score(q), "engagement": engagement_score(m)}
        sc["overall"] = overall(sc)
        presenters.append({"name": n, "metrics": m, "scores": sc, "issues": {"coverage": cov, "slide_quality": q},
                           "suggestions": suggestions(m, sc, cov, q)})
    team = None
    if mode == "group":
        from .pipeline import build_team
        spk = [{"name": p["name"], "seconds": p["metrics"]["speaking_seconds"]} for p in presenters]
        t, cur = 0, []
        for i in range(len(presenters) * 2 - 1):
            t += rnd.randint(90, 200)
            cur.append({"from": presenters[i % len(presenters)]["name"], "to": presenters[(i + 1) % len(presenters)]["name"],
                        "at": t, "gap": round(rnd.uniform(-0.3, 2.4), 1)})
        team = build_team(presenters, spk, cur, [{"slide": i + 1, "speaker": presenters[i % len(presenters)]["name"]} for i in range(8)])
    qs = [{"question": q, "related_topic": t, "rationale": r} for q, t, r in QS.get(persona, QS["General"])]
    tr = "Sample transcript (mock mode)." if store_transcript else None
    return {"presenters": presenters, "team": team, "qa": qs, "transcript": tr}
