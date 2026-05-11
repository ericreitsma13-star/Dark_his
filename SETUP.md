# Setup Guide

## 1. System dependency — FFmpeg

FFmpeg is required for chart rendering, subtitle burning, and video encoding.

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

Verify: `ffmpeg -version`

---

## 2. Python packages

```bash
pip install -r requirements.txt
```

Optional — only needed if using `TTS_ENGINE=chatterbox` (requires a CUDA GPU):
```bash
pip install chatterbox-tts
```

---

## 3. OpenRouter API key

Script generation uses [OpenRouter](https://openrouter.ai) — a single API that routes to many LLM providers.

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to **Keys** → **Create key**
3. Copy the key

Cost: ~$0.001 per video using the default model (Llama 3.3 70B).

---

## 4. Configure .env

```bash
cp .env.example .env
```

Edit `.env` — at minimum set:
```
OPENROUTER_API_KEY=sk-or-v1-...
```

Everything else has sensible defaults. See `.env.example` for all options.

---

## 5. Test run (no upload)

```bash
python main.py "The Black Death plague" --no-upload
```

This runs all 6 pipeline steps:
1. **Script** — LLM generates title, scenes, chart data
2. **Voice** — TTS narration + subtitle file
3. **Images** — one AI image per scene
4. **Chart** — animated data chart (if the topic has statistics)
5. **Assemble** — Ken Burns effect, audio mix, subtitle burn
6. **Upload** — skipped with `--no-upload`

Output video lands in `output/`. Takes 5–15 minutes on CPU, 2–5 minutes on GPU.

---

## 6. YouTube upload setup

To enable auto-upload:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the JSON file
7. Rename it to `client_secrets.json` and put it in the project root

First upload will open a browser to authorize — the token is saved to `youtube_token.pkl` after that, so subsequent uploads are fully automatic.

```bash
python main.py "The Chernobyl Disaster"   # uploads automatically
```

---

## 7. Background music (optional)

1. Download a free track from [YouTube Audio Library](https://studio.youtube.com/channel/music)
2. Save as `assets/music/background.mp3`
3. In `.env`: `BACKGROUND_MUSIC_PATH=assets/music/background.mp3`

The music is mixed at 10% volume — audible atmosphere, not distracting.

---

## 8. Batch mode

Put one topic per line in `topics.txt`, then:

```bash
python main.py --file topics.txt
```

---

## GPU setup (optional upgrade)

If you have an NVIDIA GPU:

**Voice cloning with Chatterbox:**
```bash
pip install chatterbox-tts
```
In `.env`:
```
TTS_ENGINE=chatterbox
CHATTERBOX_VOICE_REF=/path/to/10sec_voice_sample.wav   # optional, for cloning
```

**Local image generation with FLUX:**

In `.env`:
```
IMAGE_ENGINE=local-flux
```
Requires `diffusers` and ~10GB VRAM for FLUX.1-schnell.

---

## Troubleshooting

**`ffmpeg: command not found`** — install ffmpeg (step 1 above).

**`json.JSONDecodeError`** — the LLM returned malformed JSON; the pipeline retries automatically. If persistent, try a different model in `.env`.

**`OPENROUTER_API_KEY not set`** — make sure `.env` exists and contains your key.

**Images are black / missing** — Pollinations.ai may be temporarily down. The pipeline continues with a text fallback card for that scene.

**YouTube upload browser doesn't open** — run the first upload on a machine with a browser, or use `--no-upload` and upload manually.
