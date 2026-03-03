"""Pipeline orchestration: feed check -> download -> analyze -> compare."""

from __future__ import annotations

import glob
import os
from pathlib import Path

from mie.config import DOWNLOADS_DIR
from mie.ingest.downloader import download_audio
from mie.ingest.feed_monitor import Episode, get_new_episodes
from mie.schemas import ComparisonReport, PodcastAnalysis
from mie.processing.analyzer import (
    ANALYSIS_DIR,
    analyze_episode,
    compare_episodes,
    is_analyzed,
    load_cached_analyses,
)


def _find_latest_mp3(directory: Path) -> Path | None:
    """Return the most-recently-created MP3 in *directory*, or ``None``."""
    files = glob.glob(os.path.join(directory, "*.mp3"))
    if not files:
        return None
    return Path(max(files, key=os.path.getctime))


def run_pipeline(
    *,
    download_only: bool = False,
    compare: bool = True,
) -> list[Episode]:
    """Check feeds for new episodes, download, analyze, and optionally compare.

    Args:
        download_only: If True, skip Gemini analysis entirely.
        compare: If True (default), run the cross-podcast comparison after
            all episodes have been analyzed.

    Returns:
        The list of episodes that were processed.
    """
    episodes = get_new_episodes()

    if not episodes:
        print("No new episodes found across tracked channels.")
        return []

    print(f"Found {len(episodes)} new episode(s):\n")
    for ep in episodes:
        print(f"  [{ep.channel_name}] {ep.title}")
    print()

    processed: list[Episode] = []

    for ep in episodes:
        print(f"Downloading: {ep.title} ({ep.channel_name})")
        try:
            download_audio(ep.url)
        except Exception as exc:
            print(f"  Failed to download: {exc}")
            continue

        if not download_only:
            if is_analyzed(ep.video_id):
                print(f"  Already analyzed: {ep.video_id}")
            else:
                mp3 = _find_latest_mp3(DOWNLOADS_DIR)
                if mp3 is None:
                    print("  No MP3 found after download — skipping analysis.")
                    continue
                print(f"  Analyzing: {ep.title}")
                try:
                    analyze_episode(mp3, ep)
                except Exception as exc:
                    print(f"  Failed to analyze: {exc}")

        processed.append(ep)

    if not download_only and compare:
        cached = load_cached_analyses()
        if len(cached) >= 2:
            try:
                compare_episodes(cached)
            except Exception as exc:
                print(f"Comparison failed: {exc}")
        else:
            print(
                f"Skipping comparison — need at least 2 analyses, have {len(cached)}."
            )

    print(f"\nProcessed {len(processed)}/{len(episodes)} episode(s).")
    return processed
