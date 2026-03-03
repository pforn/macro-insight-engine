"""Centralised configuration for the Macro Insight Engine."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]  # repo root
DOWNLOADS_DIR: Path = PROJECT_ROOT / "downloads"
OUTPUT_DIR: Path = PROJECT_ROOT / "dump"
ARCHIVE_PATH: Path = PROJECT_ROOT / "archive.txt"
SOURCES_PATH: Path = PROJECT_ROOT / "sources.yaml"
POSITIONS_PATH: Path = PROJECT_ROOT / "positions.yaml"

# ── Gemini ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
MODEL_ID: str = "gemini-2.5-flash"

# ── Audio defaults ──────────────────────────────────────────────────────────
AUDIO_CODEC: str = "mp3"
AUDIO_QUALITY: str = "192"
