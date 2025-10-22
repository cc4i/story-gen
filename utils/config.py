
import os
from dotenv import load_dotenv

load_dotenv()

# Get the local storage path from the environment variable or use a default
LOCAL_STORAGE = os.getenv("LOCAL_STORAGE", "tmp")

# Define the subdirectories
DEFAULT_SESSION_DIR = os.path.join(LOCAL_STORAGE, "default")
CHARACTERS_DIR = os.path.join(DEFAULT_SESSION_DIR, "characters")
VIDEOS_DIR = os.path.join(DEFAULT_SESSION_DIR, "videos")

# Define the file paths
CHARACTERS_JSON = os.path.join(DEFAULT_SESSION_DIR, "characters.json")
SETTING_TXT = os.path.join(DEFAULT_SESSION_DIR, "setting.txt")
PLOT_TXT = os.path.join(DEFAULT_SESSION_DIR, "plot.txt")
STORY_JSON = os.path.join(DEFAULT_SESSION_DIR, "story.json")
MERGED_VIDEO_MP4 = os.path.join(DEFAULT_SESSION_DIR, "merged_video.mp4")

# Create the directories if they don't exist
os.makedirs(DEFAULT_SESSION_DIR, exist_ok=True)
os.makedirs(CHARACTERS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
