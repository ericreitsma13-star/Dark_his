# YouTube Autopilot

Fully automated pipeline that turns a topic into a polished, upload-ready YouTube documentary video. One command, zero manual work.

**Cost per video: ~$0.001** (script generation only — everything else is free).

## What it produces

- Animated title card with cinematic style
- 10–14 scenes with AI-generated images and Ken Burns zoom effect
- Professional voiceover (Microsoft Edge TTS or Chatterbox with voice cloning on GPU)
- Animated data chart rendered from real statistics
- Burned-in styled subtitles
- Optional background music mixed at low volume
- Outro card with subscribe CTA
- Auto-uploaded to YouTube with title, description, and tags

## Topics it handles well

Dark history · True crime · Natural disasters · Science & space · Economic collapses · Plagues & pandemics · Brutal rulers · Political upheavals

---

## Quick start

### 1. Install system dependency

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

### 2. Install Python packages

```bash
pip install -r requirements.txt
```

For GPU voice cloning (requires CUDA GPU):
```bash
pip install chatterbox-tts
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:
```
OPENROUTER_API_KEY=your_key_here
```

Get a free key at [openrouter.ai/keys](https://openrouter.ai/keys). The default model (`meta-llama/llama-3.3-70b-instruct`) costs ~$0.001 per video.

### 4. Make a video

```bash
python main.py "The Black Death plague" --no-upload
```

Output lands in `output/`. Watch it, check quality. Then run without `--no-upload` to post directly to YouTube.

---

## Usage

```bash
# Single topic
python main.py "The Rwandan Genocide"

# Skip YouTube upload
python main.py "Serial killer Ted Bundy" --no-upload

# Batch mode — one topic per line in a text file
python main.py --file topics.txt
```

---

## Configuration

All options live in `.env`. See `.env.example` for the full list.

| Variable | Default | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | — | Required. Get at openrouter.ai/keys |
| `OPENROUTER_MODEL` | `meta-llama/llama-3.3-70b-instruct` | LLM for script generation |
| `TTS_ENGINE` | `edge-tts` | `edge-tts` (CPU/free) or `chatterbox` (GPU, voice cloning) |
| `CHATTERBOX_VOICE_REF` | — | Path to a 10–20s WAV file to clone a specific voice |
| `IMAGE_ENGINE` | `pollinations` | `pollinations` (free cloud) or `local-flux` (GPU, faster) |
| `BACKGROUND_MUSIC_PATH` | — | Path to a `.mp3` to mix under narration at 10% volume |
| `YOUTUBE_CLIENT_SECRETS_FILE` | `client_secrets.json` | OAuth credentials for YouTube upload |

---

## YouTube auto-upload setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **YouTube Data API v3**
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
4. Application type: **Desktop app** → Download the JSON
5. Save it as `client_secrets.json` in the project root
6. First upload will open a browser window to authorize — token is saved after that

```bash
python main.py "The Chernobyl Disaster"   # uploads automatically
```

---

## GPU setup (RTX / CUDA)

With a CUDA GPU you can enable two upgrades:

**Voice cloning (Chatterbox):** Zero-shot — just 10–20 seconds of any narrator's voice.
```
TTS_ENGINE=chatterbox
CHATTERBOX_VOICE_REF=/path/to/reference_voice.wav
```

**Local image generation (FLUX):** Much faster than cloud, higher quality.
```
IMAGE_ENGINE=local-flux
```

---

## Project structure

```
youtube_auto/
├── main.py               # Entry point — orchestrates the 6-step pipeline
├── config.py             # All settings loaded from .env
├── pipeline/
│   ├── script_gen.py     # LLM script generation via OpenRouter
│   ├── voice_gen.py      # TTS audio + subtitle file (edge-tts or Chatterbox)
│   ├── image_gen.py      # Scene images via Pollinations.ai (or local FLUX)
│   ├── chart_gen.py      # Animated matplotlib bar chart rendered to MP4
│   ├── assembler.py      # Ken Burns clips + audio + subtitles → final MP4
│   └── uploader.py       # YouTube Data API v3 upload
├── assets/
│   └── music/            # Drop background.mp3 here
├── output/               # Final MP4s land here
├── temp/                 # Per-run working files (auto-cleaned)
├── topics.txt            # One topic per line for batch mode
├── .env.example          # Copy to .env and fill in your keys
└── requirements.txt
```

---

## Cost breakdown (per video)

| Step | Service | Cost |
|---|---|---|
| Script | OpenRouter / Llama 3.3 70B | ~$0.001 |
| Voice | Edge TTS (Microsoft) | Free |
| Images | Pollinations.ai | Free |
| Chart | matplotlib (local) | Free |
| Assembly | MoviePy + FFmpeg (local) | Free |
| Upload | YouTube Data API | Free |
| **Total** | | **~$0.001** |

At 3 videos/day that's roughly **$1/month**.

---

## Background music

Download royalty-free tracks from [YouTube Audio Library](https://studio.youtube.com/channel/music) (free for YouTube use). Save as `assets/music/background.mp3` and set the path in `.env`.
