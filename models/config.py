"""
Configuration settings for the media generation application.
"""

import os
from typing import Dict, List
from .exceptions import ConfigurationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
LOCAL_STORAGE = os.getenv("LOCAL_STORAGE", "tmp")
VEO_STORAGE_BUCKET = os.getenv("VEO_STORAGE_BUCKET", "veo-storage-bucket")
VEO_PROJECT_ID=os.getenv("VEO_PROJECT_ID")

PROJECT_ID = os.getenv("PROJECT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL_ID = os.getenv("DEFAULT_MODEL_ID", "gemini-2.0-flash")
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

SECRET_KEY = os.environ.get('SECRET_KEY')


# Validate required environment variables
def validate_config() -> None:
    """
    Validate required configuration settings.
    
    Raises:
        ConfigurationError: If required settings are missing
    """
    missing_vars = []
    if not GEMINI_API_KEY:
        missing_vars.append("GEMINI_API_KEY")
        
    if missing_vars:
        raise ConfigurationError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

# UI Constants
ASPECT_RATIOS = ["1:1", "9:16", "16:9", "4:3", "3:4"]
SAMPLE_COUNTS = ["1", "2", "3", "4", "5"]
DEFAULT_SAMPLE_COUNT = "2"
DEFAULT_ASPECT_RATIO = "16:9"

# Video Generation Constants
MIN_DURATION = 5
MAX_DURATION = 8
DEFAULT_DURATION = 8

# Model IDs
VIDEO_MODELS = ["veo-2.0-generate-001"]
IMAGE_MODELS = ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001"]

# Color mapping for harm levels
COLOR_MAP: Dict[str, str] = {
    "harmful": "crimson",
    "neutral": "gray",
    "beneficial": "green",
}

# Error messages
ERROR_MESSAGES: Dict[str, str] = {
    "file_too_large": "File size exceeds maximum allowed size",
    "invalid_model": "Invalid model ID provided",
    "generation_failed": "Failed to generate media",
    "upload_failed": "Failed to upload file",
}

# Maximum file size (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Example prompts
VIDEO_EXAMPLES: List[str] = [
    "A wide shot of a lone cowboy riding a horse across a vast, sun-drenched prairie, with a dramatic sky filled with fluffy clouds in the background. The cowboy is silhouetted against the setting sun, creating a sense of epic scale and adventure.",
    "Wide angle shot of a skier speeding down the mountain on a sunny day in the Alps.",
    "Whiteboard illustration animated video of a waiter serving food. White background, wide angle.",
]

IMAGE_EXAMPLES: List[str] = [
    "A woman, 35mm portrait, blue and grey duotones.",
    "An expansive mountain range, landscape wide angle 10mm.",
    "A technical pencil drawing of an angular sporty electric sedan with skyscrapers in the background.",
] 