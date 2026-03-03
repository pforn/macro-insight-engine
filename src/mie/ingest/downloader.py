"""Audio ingestion via yt-dlp."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yt_dlp

from mie.config import ARCHIVE_PATH, AUDIO_CODEC, AUDIO_QUALITY, DOWNLOADS_DIR


def download_audio(
    url: str,
    output_dir: Path = DOWNLOADS_DIR,
    archive_path: Path = ARCHIVE_PATH,
    codec: str = AUDIO_CODEC,
    quality: str = AUDIO_QUALITY,
) -> None:
    """Download audio from a YouTube URL and save it as an audio file.

    Args:
        url: YouTube video URL to download.
        output_dir: Directory to save the downloaded audio.
        archive_path: Path to yt-dlp's download archive (skip already-downloaded).
        codec: Target audio codec (e.g. ``mp3``).
        quality: Target audio quality in kbps.
    """
    if not output_dir.exists():
        os.makedirs(output_dir)

    ydl_opts: Any = {
        "format": "bestaudio/best",
        "download_archive": str(archive_path),
        "quiet": False,
        "no_warnings": False,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "referer": "https://www.google.com/",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": quality,
            }
        ],
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
