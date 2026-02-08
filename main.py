import os
from typing import Any

import yt_dlp


def download_audio(url: str, output_path: str = "downloads"):
    """Downloads audio from a YouTube URL and saves it as an MP3."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts: Any = {
        "format": "bestaudio/best",
        "download_archive": "archive.txt",
        "quiet": False,
        "no_warnings": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "referer": "https://www.google.com/",
        # ⬆️
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    # Test with one of our macro podcast links
    test_url = "https://www.youtube.com/watch?v=7WrpqjcMCWI"
    download_audio(test_url)
