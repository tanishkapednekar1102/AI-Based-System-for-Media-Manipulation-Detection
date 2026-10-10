import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Storage Directories
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
REPORTS_DIR = BASE_DIR / "results" / "pdf_reports"
DATASET_DIR = BASE_DIR / "dataset"
MODELS_DIR = BASE_DIR / "models"

IMAGE_MODEL_PATH = MODELS_DIR / "image_model" / "image_model.h5"
VIDEO_MODEL_PATH = MODELS_DIR / "video_model" / "video_model.h5"
AUDIO_MODEL_PATH = MODELS_DIR / "audio_model" / "audio_model.h5"

# Ensure runtime directories exist
for folder in [UPLOAD_DIR, RESULTS_DIR, REPORTS_DIR, DATASET_DIR, MODELS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Database Configurations
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "media_manipulation_detection")

import socket

def find_available_port(default_port=8080):
    """Checks if default_port is free. If occupied, finds the next available port."""
    port = default_port
    while port < default_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(('127.0.0.1', port))
            if res != 0:  # Port is free
                return port
            port += 1
    return default_port

# Application Details
APP_TITLE = "AI-Based System for Media Manipulation Detection"
APP_SUBTITLE = "Detect. Analyze. Verify Digital Media."
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
PREFERRED_PORT = int(os.getenv("APP_PORT", 8080))
APP_PORT = find_available_port(PREFERRED_PORT)
SECRET_KEY = os.getenv("SECRET_KEY", "media-forensics-secret-key-2026")


# Detection Thresholds & Settings
UNCERTAIN_LOWER = 0.40
UNCERTAIN_UPPER = 0.60
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}
ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a"}

# Theme Colors (Dark Navy & Cyber-Forensics Aesthetic)
COLORS = {
    "bg_dark": "#0B132B",
    "card_dark": "#1C2541",
    "navy_header": "#0A1128",
    "accent_blue": "#1282A2",
    "accent_cyan": "#00B4D8",
    "accent_bright": "#0077B6",
    "text_white": "#FEFCFB",
    "text_muted": "#A0AEC0",
    "authentic": "#10B981",    # Emerald green
    "manipulated": "#EF4444",  # Red
    "synthetic": "#F59E0B",    # Amber
    "uncertain": "#6B7280"     # Gray
}
