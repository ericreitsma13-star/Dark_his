import asyncio
import shutil
from config import NARRATOR_VOICE, TTS_ENGINE, CHATTERBOX_VOICE_REF


# ── Edge-TTS backend (CPU, free, no GPU needed) ───────────────────────────────

async def _edge_generate(text: str, audio_path: str, srt_path: str, voice: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(submaker.get_srt())


def _edge_tts(text: str, audio_path: str, srt_path: str, voice: str):
    asyncio.run(_edge_generate(text, audio_path, srt_path, voice))


# ── Chatterbox backend (CUDA GPU, voice cloning) ──────────────────────────────

def _chatterbox_tts(text: str, audio_path: str, srt_path: str):
    import torch
    import torchaudio
    from chatterbox.tts import ChatterboxTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)

    ref = CHATTERBOX_VOICE_REF if CHATTERBOX_VOICE_REF else None
    wav = model.generate(text, audio_prompt_path=ref, exaggeration=0.45)

    # Save as WAV first, then convert to MP3 via ffmpeg
    wav_tmp = audio_path.replace(".mp3", "_tmp.wav")
    torchaudio.save(wav_tmp, wav, model.sr)

    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-i", wav_tmp, "-q:a", "2", audio_path],
        check=True, capture_output=True,
    )
    import os
    os.remove(wav_tmp)

    # Generate sentence-level SRT from text (Chatterbox has no word timestamps)
    _write_naive_srt(text, audio_path, srt_path)


def _write_naive_srt(text: str, audio_path: str, srt_path: str):
    """Fallback: split text into sentences, estimate timing from audio duration."""
    import subprocess, re, math

    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True,
    )
    total_sec = float(result.stdout.strip()) if result.stdout.strip() else 60.0

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentences:
        open(srt_path, "w").close()
        return

    dur_each = total_sec / len(sentences)
    lines = []
    for i, sentence in enumerate(sentences):
        start = i * dur_each
        end = start + dur_each
        lines.append(f"{i+1}")
        lines.append(f"{_fmt(start)} --> {_fmt(end)}")
        lines.append(sentence)
        lines.append("")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _fmt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ── Public interface ──────────────────────────────────────────────────────────

def generate_voice(text: str, audio_path: str, vtt_path: str, voice: str = NARRATOR_VOICE):
    """Generate narration audio + SRT (written to vtt_path for pipeline compat)."""
    if TTS_ENGINE == "chatterbox":
        _chatterbox_tts(text, audio_path, vtt_path)
    else:
        _edge_tts(text, audio_path, vtt_path, voice)


def vtt_to_srt(vtt_path: str, srt_path: str):
    shutil.copy2(vtt_path, srt_path)
