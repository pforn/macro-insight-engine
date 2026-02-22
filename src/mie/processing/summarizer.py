"""Audio-to-summary orchestration logic.

This module contains the pure business logic extracted from the old
``synthesis.py``: find the latest audio file, upload it, summarise it,
and print/save the result.  All Gemini I/O is delegated to
:mod:`mie.processing.gemini_client` so this module can be tested without
network calls.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

from mie.config import DOWNLOADS_DIR, GEMINI_API_KEY, MODEL_ID
from mie.processing import gemini_client
from mie.prompts import SYSTEM_PROMPT


def summarize_latest_audio(directory: Path = DOWNLOADS_DIR) -> str | None:
    """Find the newest MP3 in *directory*, upload it to Gemini, and summarise.

    The function temporarily renames the file to an ASCII-safe name to avoid
    encoding issues during upload, then restores the original name afterward.

    Args:
        directory: Folder containing downloaded audio files.

    Returns:
        The generated summary text, or ``None`` if no MP3 was found.
    """
    files = glob.glob(os.path.join(directory, "*.mp3"))
    if not files:
        print("No MP3 files found to process.")
        return None

    latest_file = max(files, key=os.path.getctime)
    print(f"Processing: {latest_file}")

    # Rename to a safe filename to avoid encoding issues with special chars
    file_ext = os.path.splitext(latest_file)[1]
    safe_path = os.path.join(directory, f"temp_processing{file_ext}")
    os.rename(latest_file, safe_path)

    try:
        client = gemini_client.get_client(GEMINI_API_KEY)

        print("Uploading to Gemini...")
        audio_file = gemini_client.upload_file(client, safe_path)
        audio_file = gemini_client.wait_for_processing(client, audio_file)

        user_prompt = (
            "Please provide a comprehensive summary of this audio recording. "
            f"Original title: {os.path.basename(latest_file)}"
        )

        print("Generating summary...")
        summary = gemini_client.generate_summary(
            client=client,
            model=MODEL_ID,
            audio_file=audio_file,
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
        )

        print(f"\n✅ Summary:\n{summary}")
        return summary

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Restore original filename
        if os.path.exists(safe_path):
            os.rename(safe_path, latest_file)
