"""CLI entry point for the Macro Insight Engine."""

from __future__ import annotations

from mie.ingest.downloader import download_audio
from mie.processing.summarizer import summarize_latest_audio


def main() -> None:
    """Run the full download → summarise pipeline."""
    # TODO: accept URL(s) from CLI args / sources.json registry
    test_url = "https://www.youtube.com/watch?v=7WrpqjcMCWI"

    print("🔽  Downloading audio...")
    download_audio(test_url)

    print("\n🤖  Summarising...")
    summarize_latest_audio()


if __name__ == "__main__":
    main()
