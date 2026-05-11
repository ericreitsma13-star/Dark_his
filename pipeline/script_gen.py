import json
import re
import os
import requests
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL


def _sanitize_json_strings(s: str) -> str:
    """Escape bare control characters that appear inside JSON string values."""
    result = []
    in_string = False
    escape_next = False
    ctrl_map = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}
    for ch in s:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == '\\':
            result.append(ch)
            escape_next = True
        elif ch == '"':
            result.append(ch)
            in_string = not in_string
        elif in_string and ord(ch) < 0x20:
            result.append(ctrl_map.get(ch, f'\\u{ord(ch):04x}'))
        else:
            result.append(ch)
    return ''.join(result)


SYSTEM_PROMPT = """You are a world-class documentary scriptwriter for a viral YouTube channel.
You create compelling, factual, and deeply researched scripts on topics including:
- Dark history, massacres, and brutal rulers
- Serial killers and true crime
- Natural disasters and catastrophes
- Science discoveries and space exploration
- Economic collapses and political upheavals
- Biological events (plagues, pandemics)

Your scripts are gripping from the first word, use vivid language, and maintain tension throughout.
You always return valid JSON — nothing else, no markdown, no explanation."""


SCRIPT_PROMPT = """Create a viral YouTube documentary script about: "{topic}"

Return ONLY valid JSON in this exact structure:
{{
  "title": "Compelling YouTube title (max 70 chars, hooks the viewer)",
  "description": "YouTube description (2-3 paragraphs, include chapter markers if applicable)",
  "tags": ["tag1", "tag2", "..."],
  "thumbnail_concept": "One sentence describing a dramatic thumbnail image",
  "scenes": [
    {{
      "id": 1,
      "narration": "The narration text for this scene (2-4 sentences, gripping)",
      "image_prompt": "Extremely detailed cinematic image prompt: setting, lighting, style, era, mood. Start with 'cinematic documentary still, '",
      "duration_seconds": 12
    }}
  ],
  "chart": {{
    "title": "Chart title showing comparative data",
    "subtitle": "e.g. Number of victims by event/period",
    "insert_after_scene": 4,
    "data": [
      {{"label": "Event or name", "value": 0, "color": "#c0392b"}}
    ]
  }}
}}

Rules:
- Total script should be 6-8 minutes (roughly 900-1200 words across all narrations)
- 10-14 scenes total
- image_prompt must be historically accurate and cinematic — dark, atmospheric, high contrast
- chart data must have real, researchable numbers (deaths, dates, quantities)
- chart colors: use dramatic reds (#c0392b), dark oranges (#e67e22), deep purples (#8e44ad)
- The chart insert_after_scene should be where data comparison makes most narrative sense
"""


def generate_script(topic: str) -> dict:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": SCRIPT_PROMPT.format(topic=topic)},
        ],
        "max_tokens": 8192,
        "temperature": 0.8,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/youtube-autopilot",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if model wrapped in them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    # Sanitize unescaped control characters inside JSON string values
    raw = _sanitize_json_strings(raw)

    data = json.loads(raw)

    required = {"title", "description", "tags", "scenes", "chart"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Response missing keys: {missing}")

    return data
