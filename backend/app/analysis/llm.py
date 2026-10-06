import json
import re
import httpx
from .. import config


def chat_json(system: str, user: str):
    """Calls an OpenAI-compatible chat endpoint (Sarvam by default). Returns parsed JSON or None."""
    if not config.LLM_API_KEY:
        return None
    try:
        r = httpx.post(
            config.LLM_BASE_URL + "/chat/completions",
            headers={"api-subscription-key": config.LLM_API_KEY, "Authorization": f"Bearer {config.LLM_API_KEY}"},
            json={"model": config.LLM_MODEL, "temperature": 0.3,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
            timeout=120)
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"]
        txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.S)
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else None
    except Exception as ex:  # never break the pipeline because of the LLM
        print("[llm] failed:", ex)
        return None


SYSTEM = ("You are an expert presentation coach acting as a tough but fair audience. "
          "Reply with ONLY a JSON object, no markdown.")


def semantic_analysis(transcript: str, slides: list, persona: str, want_qa: bool):
    slide_txt = "\n".join(f"[Slide {i}] {s[:600]}" for i, s in enumerate(slides, 1))[:9000]
    prompt = f"""Audience persona: {persona}.
Transcript of the talk:
{transcript[:12000]}

Slides:
{slide_txt or '(no slides provided)'}

Return JSON with keys:
"coverage": list of {{"slide": int, "status": "strong"|"insufficient"|"verbatim"|"skipped", "note": short sentence}} (one per slide, empty if no slides),
"skipped_topics": list of short strings,
"summary": 2 sentence overall impression,
"questions": {"list of exactly 5 {question, related_topic, rationale} tailored to the persona and the gaps in the talk" if want_qa else "[]"}"""
    return chat_json(SYSTEM, prompt)
