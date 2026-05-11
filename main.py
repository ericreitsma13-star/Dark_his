#!/usr/bin/env python3
"""
YouTube Autopilot
Usage:
  python main.py "The Rwandan Genocide"
  python main.py --file topics.txt           # batch mode: one topic per line
  python main.py "Black Death plague" --no-upload
"""

import sys
import os
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime

from config import (
    OUTPUT_DIR, TEMP_DIR,
    BACKGROUND_MUSIC_PATH, YOUTUBE_CLIENT_SECRETS_FILE,
    OPENROUTER_API_KEY,
)
from pipeline.script_gen import generate_script
from pipeline.voice_gen import generate_voice, vtt_to_srt
from pipeline.image_gen import generate_images_batch
from pipeline.chart_gen import render_chart
from pipeline.assembler import assemble_video
from pipeline.uploader import upload_video


def slug(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def produce_video(topic: str, upload: bool = True) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_slug = slug(topic)
    run_dir = Path(TEMP_DIR) / f"{ts}_{video_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f" Topic: {topic}")
    print(f"{'='*60}")

    # ── 1. Script ──────────────────────────────────────────────
    print("\n[1/6] Generating script with Gemini...")
    script = generate_script(topic)
    script_file = run_dir / "script.json"
    script_file.write_text(json.dumps(script, indent=2))
    print(f"  Title: {script['title']}")
    print(f"  Scenes: {len(script['scenes'])}")

    # ── 2. Voice + Subtitles ───────────────────────────────────
    print("\n[2/6] Generating voiceover...")
    full_narration = " ".join(s["narration"] for s in script["scenes"])
    audio_path = str(run_dir / "narration.mp3")
    vtt_path = str(run_dir / "subtitles.vtt")
    srt_path = str(run_dir / "subtitles.srt")
    generate_voice(full_narration, audio_path, vtt_path)
    vtt_to_srt(vtt_path, srt_path)
    print("  Done.")

    # ── 3. Images ──────────────────────────────────────────────
    print("\n[3/6] Generating scene images...")
    images_dir = str(run_dir / "images")
    image_paths = generate_images_batch(script["scenes"], images_dir)
    ok = sum(1 for v in image_paths.values() if v)
    print(f"  {ok}/{len(script['scenes'])} images generated.")

    # ── 4. Chart ───────────────────────────────────────────────
    chart_path = None
    if script.get("chart") and script["chart"].get("data"):
        print("\n[4/6] Rendering data chart...")
        chart_path = str(run_dir / "chart.mp4")
        render_chart(script["chart"], chart_path)
    else:
        print("\n[4/6] No chart data — skipping.")

    # ── 5. Assemble ────────────────────────────────────────────
    print("\n[5/6] Assembling final video...")
    final_path = str(out_dir / f"{ts}_{video_slug}.mp4")
    music_path = BACKGROUND_MUSIC_PATH if BACKGROUND_MUSIC_PATH else None

    assemble_video(
        script_data=script,
        image_paths=image_paths,
        audio_path=audio_path,
        srt_path=srt_path,
        chart_path=chart_path,
        music_path=music_path,
        output_path=final_path,
        temp_dir=str(run_dir),
    )

    # ── 6. Upload ──────────────────────────────────────────────
    url = None
    if upload and os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
        print("\n[6/6] Uploading to YouTube...")
        url = upload_video(
            video_path=final_path,
            title=script["title"],
            description=script["description"],
            tags=script["tags"],
            client_secrets_file=YOUTUBE_CLIENT_SECRETS_FILE,
        )
    elif upload:
        print("\n[6/6] Upload skipped — client_secrets.json not found.")
        print("  Follow setup guide in README to enable auto-upload.")
    else:
        print("\n[6/6] Upload skipped (--no-upload flag).")

    # Save metadata
    meta = {
        "topic": topic,
        "title": script["title"],
        "description": script["description"],
        "tags": script["tags"],
        "video_path": final_path,
        "youtube_url": url,
    }
    (out_dir / f"{ts}_{video_slug}.json").write_text(json.dumps(meta, indent=2))

    print(f"\n{'='*60}")
    print(f" DONE: {final_path}")
    if url:
        print(f" YouTube: {url}")
    print(f"{'='*60}\n")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="YouTube Autopilot — one topic, one video")
    parser.add_argument("topic", nargs="?", help="Topic to make a video about")
    parser.add_argument("--file", help="Text file with one topic per line (batch mode)")
    parser.add_argument("--no-upload", action="store_true", help="Skip YouTube upload")
    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set.")
        print("1. Go to https://openrouter.ai/keys")
        print("2. Create an API key")
        print("3. Copy key into your .env file as OPENROUTER_API_KEY=...")
        sys.exit(1)

    topics = []
    if args.file:
        topics = [line.strip() for line in open(args.file) if line.strip()]
    elif args.topic:
        topics = [args.topic]
    else:
        parser.print_help()
        sys.exit(1)

    for topic in topics:
        produce_video(topic, upload=not args.no_upload)


if __name__ == "__main__":
    main()
