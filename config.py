import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
BACKGROUND_MUSIC_PATH = os.getenv("BACKGROUND_MUSIC_PATH", "")

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 24

NARRATOR_VOICE = "en-GB-SoniaNeural"   # Deep, serious documentary voice
SUBTITLE_WORDS_PER_CUE = 5             # Words shown at once in subtitles
BG_MUSIC_VOLUME = 0.10                 # 10% — audible but not distracting

TTS_ENGINE = os.getenv("TTS_ENGINE", "edge-tts")          # "edge-tts" or "chatterbox"
CHATTERBOX_VOICE_REF = os.getenv("CHATTERBOX_VOICE_REF", "")  # path to 10-20s WAV for voice cloning
IMAGE_ENGINE = os.getenv("IMAGE_ENGINE", "pollinations")   # "pollinations" or "local-flux"

OUTPUT_DIR = "output"
TEMP_DIR = "temp"
