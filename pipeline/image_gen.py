import requests
import urllib.parse
import time
from pathlib import Path


def generate_image(prompt: str, output_path: str, seed: int = 42, retries: int = 3) -> bool:
    """
    Download an AI-generated image from Pollinations.ai — completely free, no API key.
    Falls back gracefully if the service is unavailable.
    """
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1920&height=1080&nologo=true&seed={seed}&model=flux"

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200 and len(response.content) > 10_000:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
        except requests.RequestException:
            pass

        if attempt < retries - 1:
            time.sleep(3)

    print(f"  [warn] Image generation failed for: {prompt[:60]}...")
    return False


def generate_images_batch(scenes: list[dict], temp_dir: str) -> dict[int, str]:
    """
    Generate one image per scene. Returns {scene_id: image_path}.
    Uses scene id as seed variation so each image is unique.
    """
    results = {}
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    for scene in scenes:
        scene_id = scene["id"]
        prompt = scene["image_prompt"]
        output_path = str(Path(temp_dir) / f"scene_{scene_id:02d}.jpg")

        print(f"  Generating image {scene_id}/{len(scenes)}: {prompt[:60]}...")
        ok = generate_image(prompt, output_path, seed=scene_id * 17)

        if ok:
            results[scene_id] = output_path
        else:
            results[scene_id] = None

    return results
