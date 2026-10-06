"""Speech-to-text + speaker diarization using Sarvam AI Batch API."""
import json
import subprocess
from pathlib import Path
from .. import config


def to_wav(src: Path, workdir: Path) -> Path:
    """Extract/convert any audio or video to 16 kHz mono WAV using bundled ffmpeg."""
    import imageio_ffmpeg
    out = workdir / "audio.wav"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
           "-c:a", "pcm_s16le", str(out)]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError("Could not read audio from the uploaded file: " + r.stderr.decode(errors="ignore")[-300:])
    return out


def transcribe(wav: Path, workdir: Path, diarize: bool, num_speakers=None, language=None):
    """Returns {'entries': [{'text','start','end','speaker'}], 'language': str}."""
    from sarvamai import SarvamAI
    client = SarvamAI(api_subscription_key=config.SARVAM_API_KEY)
    kw = dict(model=config.STT_MODEL, mode=config.STT_MODE, language_code=language or config.STT_LANGUAGE,
              with_diarization=diarize, with_timestamps=True)
    if diarize and num_speakers:
        kw["num_speakers"] = int(num_speakers)
    job = client.speech_to_text_job.create_job(**kw)
    job.upload_files(file_paths=[str(wav)])
    job.start()
    job.wait_until_complete(poll_interval=5, timeout=config.STT_TIMEOUT)
    res = job.get_file_results()
    if not res["successful"]:
        err = res["failed"][0].get("error_message") if res["failed"] else "unknown error"
        raise RuntimeError(f"Sarvam transcription failed: {err}")
    out = workdir / "stt"
    out.mkdir(exist_ok=True)
    job.download_outputs(output_dir=str(out))
    files = sorted(out.rglob("*.json"))
    if not files:
        raise RuntimeError("Sarvam returned no output files")
    data = json.loads(files[0].read_text(encoding="utf-8"))
    entries = []
    dz = (data.get("diarized_transcript") or {}).get("entries") or []
    for e in dz:
        entries.append({"text": e.get("transcript", ""), "start": float(e.get("start_time_seconds", 0)),
                        "end": float(e.get("end_time_seconds", 0)), "speaker": str(e.get("speaker_id", "0"))})
    if not entries:  # no diarization -> use plain chunks as one speaker
        ts = data.get("timestamps") or {}
        for t, s, e in zip(ts.get("chunks", []), ts.get("start_time_seconds", []), ts.get("end_time_seconds", [])):
            entries.append({"text": t, "start": float(s), "end": float(e), "speaker": "0"})
    if not entries and data.get("transcript"):
        entries.append({"text": data["transcript"], "start": 0.0, "end": 60.0, "speaker": "0"})
    entries.sort(key=lambda x: x["start"])
    return {"entries": entries, "language": data.get("language_code")}
