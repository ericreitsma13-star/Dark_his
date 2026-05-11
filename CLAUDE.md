# Project Context for Claude

## What this is

Automated YouTube documentary video pipeline. One command turns a topic into a polished, upload-ready MP4. See README.md for full details.

## Stack

- **Script generation**: OpenRouter API (Llama 3.3 70B, ~$0.001/video)
- **TTS**: edge-tts (CPU) or Chatterbox (CUDA GPU, voice cloning)
- **Images**: Pollinations.ai free API (no key needed) or local FLUX
- **Chart**: matplotlib animated bar chart → MP4
- **Assembly**: MoviePy 1.0.3 + FFmpeg (Ken Burns effect, subtitle burn)
- **Upload**: YouTube Data API v3

## Current state (as of May 2026)

Pipeline is fully coded and tested end-to-end. All steps work except:

- **ffmpeg not yet installed on laptop** — run `sudo apt install ffmpeg` first
- **YouTube upload not configured** — needs `client_secrets.json` (see SETUP.md)
- **Subtitles empty on first test run** — was a bug, now fixed (edge-tts SubMaker API changed: events are `SentenceBoundary` not `WordBoundary`, method is `feed()` + `get_srt()`)

## First thing to do on a new machine

```bash
sudo apt install ffmpeg
pip install -r requirements.txt
pip install chatterbox-tts        # if CUDA GPU available
cp .env.example .env              # then add OpenRouter key
python main.py "The Black Death plague" --no-upload
```

## Known bugs already fixed (do not reintroduce)

- `script_gen.py`: Llama 3.3 70B returns JSON with literal control characters inside strings — fixed with `_sanitize_json_strings()` character-by-character parser before `json.loads()`
- `voice_gen.py`: old edge-tts used `create_sub()` + `generate_subs()` — new API uses `submaker.feed(chunk)` + `submaker.get_srt()`. Feed both `WordBoundary` and `SentenceBoundary` chunk types.
- `.env` model was `google/gemini-2.5-flash-preview` which doesn't exist on OpenRouter — correct model is `meta-llama/llama-3.3-70b-instruct`

## GPU upgrades (RTX 4090 laptop)

Set in `.env`:
```
TTS_ENGINE=chatterbox
CHATTERBOX_VOICE_REF=/path/to/10sec_voice_sample.wav   # optional, for voice cloning
IMAGE_ENGINE=local-flux                                  # faster, higher quality images
```

`local-flux` backend not yet implemented in `image_gen.py` — needs to be added using `diffusers` + FLUX.1-schnell.

## Pipeline flow (main.py)

1. `script_gen.py` → JSON with title, scenes (narration + image_prompt + duration), chart data
2. `voice_gen.py` → narration.mp3 + subtitles.srt
3. `image_gen.py` → scene_01.jpg … scene_N.jpg
4. `chart_gen.py` → chart.mp4 (skipped if no chart data)
5. `assembler.py` → final MP4 with Ken Burns, audio mix, burned subtitles
6. `uploader.py` → YouTube (skipped if no client_secrets.json or --no-upload)

## OpenRouter key

Get from openrouter.ai/keys — same account already in use. Add to `.env` as `OPENROUTER_API_KEY`.
