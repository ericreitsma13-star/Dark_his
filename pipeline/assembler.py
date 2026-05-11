import os
import subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
from moviepy.editor import (
    AudioFileClip,
    VideoFileClip,
    ImageClip,
    ColorClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    AudioFileClip,
    CompositeAudioClip,
    afx,
)
from config import VIDEO_WIDTH, VIDEO_HEIGHT, FPS, BG_MUSIC_VOLUME

W, H = VIDEO_WIDTH, VIDEO_HEIGHT
TRANSITION_DURATION = 0.5


# ─── Ken Burns Effect ───────────────────────────────────────────────────────────

def _ken_burns_frames(img_path: str, duration: float, fps: int, zoom: float = 1.06) -> np.ndarray:
    """Return array of frames with slow zoom + subtle pan."""
    img = Image.open(img_path).convert("RGB")

    # Cinematic color grade: darken + slight blue tint
    img = ImageEnhance.Brightness(img).enhance(0.80)
    r, g, b = img.split()
    b = ImageEnhance.Brightness(b).enhance(1.08)
    img = Image.merge("RGB", (r, g, b))

    # Upscale to allow zoom without quality loss
    zoomed_w = int(W * zoom)
    zoomed_h = int(H * zoom)
    img = img.resize((zoomed_w, zoomed_h), Image.LANCZOS)

    n_frames = int(duration * fps)
    frames = []

    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        # Subtle pan: drift diagonally from top-left to center
        max_x = zoomed_w - W
        max_y = zoomed_h - H
        x = int(max_x * t * 0.5)
        y = int(max_y * t * 0.5)
        cropped = img.crop((x, y, x + W, y + H))
        frames.append(np.array(cropped))

    return frames


def make_scene_clip(img_path: str, duration: float) -> ImageClip:
    frames = _ken_burns_frames(img_path, duration, FPS)
    from moviepy.editor import ImageSequenceClip
    clip = ImageSequenceClip(frames, fps=FPS)
    return clip.fadein(TRANSITION_DURATION).fadeout(TRANSITION_DURATION)


# ─── Title Card ─────────────────────────────────────────────────────────────────

def make_title_card(title: str, duration: float = 4.0) -> CompositeVideoClip:
    bg = ColorClip((W, H), color=(0, 0, 0)).set_duration(duration)

    # Thin accent bar
    bar = ColorClip((W, 4), color=(180, 20, 20)).set_duration(duration).set_position(("center", H // 2 - 60))

    title_clip = (
        TextClip(title, fontsize=72, color="white", font="DejaVu-Sans-Bold",
                 size=(W - 200, None), method="caption", align="center")
        .set_duration(duration)
        .set_position("center")
        .fadein(0.6)
        .fadeout(0.4)
    )

    return CompositeVideoClip([bg, bar, title_clip]).fadein(0.4).fadeout(0.4)


# ─── Outro Card ─────────────────────────────────────────────────────────────────

def make_outro_card(duration: float = 4.0) -> CompositeVideoClip:
    bg = ColorClip((W, H), color=(8, 8, 8)).set_duration(duration)
    cta = (
        TextClip("Like · Subscribe · Share", fontsize=58, color="#c0392b",
                 font="DejaVu-Sans-Bold")
        .set_duration(duration)
        .set_position(("center", H // 2 - 40))
        .fadein(0.5)
    )
    sub = (
        TextClip("New video every week", fontsize=32, color="#888888",
                 font="DejaVu-Sans")
        .set_duration(duration)
        .set_position(("center", H // 2 + 40))
        .fadein(0.8)
    )
    return CompositeVideoClip([bg, cta, sub]).fadein(0.4)


# ─── Fallback Image (if generation failed) ──────────────────────────────────────

def _make_fallback_clip(text: str, duration: float) -> CompositeVideoClip:
    bg = ColorClip((W, H), color=(10, 10, 10)).set_duration(duration)
    txt = (
        TextClip(text[:80], fontsize=36, color="#666666", font="DejaVu-Sans",
                 size=(W - 200, None), method="caption", align="center")
        .set_duration(duration)
        .set_position("center")
    )
    return CompositeVideoClip([bg, txt])


# ─── Main Assembler ──────────────────────────────────────────────────────────────

def assemble_video(
    script_data: dict,
    image_paths: dict,
    audio_path: str,
    srt_path: str,
    chart_path: str | None,
    music_path: str | None,
    output_path: str,
    temp_dir: str,
):
    print("  Building video clips...")

    title_card = make_title_card(script_data["title"])
    outro_card = make_outro_card()

    chart_insert_after = script_data.get("chart", {}).get("insert_after_scene", 999)
    scene_clips = []

    for scene in script_data["scenes"]:
        sid = scene["id"]
        duration = float(scene.get("duration_seconds", 10))
        img_path = image_paths.get(sid)

        if img_path and os.path.exists(img_path):
            clip = make_scene_clip(img_path, duration)
        else:
            clip = _make_fallback_clip(scene["narration"][:80], duration)

        scene_clips.append(clip)

        # Insert chart video after specified scene
        if sid == chart_insert_after and chart_path and os.path.exists(chart_path):
            chart_clip = VideoFileClip(chart_path).fadein(0.5).fadeout(0.5)
            scene_clips.append(chart_clip)

    all_clips = [title_card] + scene_clips + [outro_card]
    video = concatenate_videoclips(all_clips, method="compose")

    # Narration audio
    narration = AudioFileClip(audio_path)

    # Background music (optional)
    if music_path and os.path.exists(music_path):
        music = (
            AudioFileClip(music_path)
            .volumex(BG_MUSIC_VOLUME)
            .audio_loop(duration=video.duration)
            .audio_fadeout(2.0)
        )
        final_audio = CompositeAudioClip([music, narration.set_start(title_card.duration)])
    else:
        final_audio = narration.set_start(title_card.duration)

    video = video.set_audio(final_audio)

    # Write without subtitles first
    raw_path = str(Path(temp_dir) / "raw_video.mp4")
    print("  Rendering video (this takes a few minutes)...")
    video.write_videofile(
        raw_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="6000k",
        threads=4,
        preset="fast",
        logger=None,
    )

    # Burn in subtitles with FFmpeg
    if srt_path and os.path.exists(srt_path):
        print("  Burning subtitles...")
        subtitle_style = (
            "FontName=DejaVu Sans Bold,FontSize=22,Bold=1,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            "BackColour=&H80000000,BorderStyle=4,"
            "Outline=2,Shadow=1,Alignment=2,"
            "MarginV=40"
        )
        safe_srt = srt_path.replace(":", "\\:")
        cmd = [
            "ffmpeg", "-y",
            "-i", raw_path,
            "-vf", f"subtitles={safe_srt}:force_style='{subtitle_style}'",
            "-c:a", "copy",
            "-preset", "fast",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  [warn] Subtitle burn failed, using raw video. Error: {result.stderr[-200:]}")
            os.replace(raw_path, output_path)
        else:
            os.remove(raw_path)
    else:
        os.replace(raw_path, output_path)

    print(f"  Final video: {output_path}")
