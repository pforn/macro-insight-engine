"""CLI entry point for the Macro Insight Engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from mie.config import SOURCES_PATH
from mie.ingest.feed_monitor import ChannelConfig, Episode, get_new_episodes, load_sources
from mie.ingest.pipeline import run_pipeline
from mie.processing.analyzer import (
    ANALYSIS_DIR,
    analyze_episode,
    compare_episodes,
    load_cached_analyses,
)


def _cmd_check(args: argparse.Namespace) -> None:
    """List new (unprocessed) episodes without downloading."""
    episodes = get_new_episodes()

    if not episodes:
        print("No new episodes found.")
        return

    print(f"Found {len(episodes)} new episode(s):\n")
    for ep in episodes:
        print(f"  [{ep.channel_name}] {ep.title}")
        print(f"    {ep.url}  ({ep.published})")
    print()


def _cmd_run(args: argparse.Namespace) -> None:
    """Run the full pipeline: check feeds, download, analyze, and compare."""
    run_pipeline(
        download_only=args.download_only,
        compare=not args.no_compare,
    )


def _cmd_sources(args: argparse.Namespace) -> None:
    """List all tracked channels and their status."""
    path = SOURCES_PATH
    if not path.exists():
        print(f"No sources file found at {path}")
        return

    with open(path) as f:
        data = yaml.safe_load(f)

    channels = data.get("channels", [])
    print(f"Tracking {len(channels)} channel(s):\n")
    for ch in channels:
        status = "enabled" if ch.get("enabled", True) else "disabled"
        kw = ch.get("keywords", [])
        kw_str = f'  keywords: {", ".join(kw)}' if kw else ""
        print(f"  [{status}] {ch['name']} ({ch['channel_id']}){kw_str}")
    print()


def _cmd_analyze(args: argparse.Namespace) -> None:
    """Run Pass 1 (structured extraction) on a specific MP3 file."""
    audio = Path(args.file).resolve()
    if not audio.is_file():
        print(f"File not found: {audio}", file=sys.stderr)
        sys.exit(1)

    episode = Episode(
        video_id=args.episode_id or audio.stem,
        url="",
        title=args.title or audio.stem,
        channel_name=args.channel or "unknown",
        published=args.published or "",
    )

    analysis = analyze_episode(audio, episode)
    if args.json:
        print(analysis.model_dump_json(indent=2))
    else:
        print(f"\nAnalysis complete: {analysis.episode_id}")
        print(f"  Topics: {len(analysis.topics)}")
        print(f"  Claims: {len(analysis.key_claims)}")
        print(f"  Sentiment: {analysis.overall_sentiment}")


def _cmd_compare(args: argparse.Namespace) -> None:
    """Run Pass 2 (cross-podcast comparison) on cached analyses."""
    analyses = load_cached_analyses()
    if len(analyses) < 2:
        print(
            f"Need at least 2 cached analyses to compare, found {len(analyses)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Comparing {len(analyses)} episode(s)...")
    report = compare_episodes(analyses)

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"\nComparison complete ({report.period})")
        print(f"  Consensus topics: {len(report.consensus_topics)}")
        print(f"  Controversial topics: {len(report.controversial_topics)}")
        print(f"  Unique insights: {len(report.unique_insights)}")
        print(f"  Overall sentiment: {report.overall_market_sentiment}")


def _cmd_add(args: argparse.Namespace) -> None:
    """Add a new YouTube channel to sources.yaml."""
    import yt_dlp

    url = args.channel_url
    print(f"Resolving channel info from: {url}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlist_items": "1",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        print(f"Failed to resolve channel: {exc}", file=sys.stderr)
        sys.exit(1)

    if info is None:
        print("Could not retrieve channel info.", file=sys.stderr)
        sys.exit(1)

    channel_id = info.get("channel_id") or ""
    channel_name = info.get("channel") or info.get("uploader") or ""

    if not channel_id:
        print("Could not determine channel ID.", file=sys.stderr)
        sys.exit(1)

    if SOURCES_PATH.exists():
        with open(SOURCES_PATH) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    channels = data.setdefault("channels", [])

    for existing in channels:
        if existing.get("channel_id") == channel_id:
            print(f"Channel already tracked: {existing['name']} ({channel_id})")
            return

    new_entry = {
        "name": channel_name,
        "channel_id": channel_id,
        "keywords": [],
        "enabled": True,
    }
    channels.append(new_entry)

    with open(SOURCES_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"Added: {channel_name} ({channel_id})")


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate subcommand."""
    parser = argparse.ArgumentParser(
        prog="mie",
        description="Macro Insight Engine - automated macro podcast analysis",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="List new episodes without downloading")

    run_parser = sub.add_parser("run", help="Download, analyze, and compare new episodes")
    run_parser.add_argument(
        "--download-only",
        action="store_true",
        default=False,
        help="Download audio without running Gemini analysis",
    )
    run_parser.add_argument(
        "--no-compare",
        action="store_true",
        default=False,
        help="Skip the cross-podcast comparison after analysis",
    )

    analyze_parser = sub.add_parser("analyze", help="Run structured analysis on an MP3 file")
    analyze_parser.add_argument("file", help="Path to the MP3 file to analyze")
    analyze_parser.add_argument("--episode-id", help="Override episode ID (default: filename stem)")
    analyze_parser.add_argument("--title", help="Override episode title")
    analyze_parser.add_argument("--channel", help="Override channel name")
    analyze_parser.add_argument("--published", help="Override publish date (ISO format)")
    analyze_parser.add_argument("--json", action="store_true", help="Print full JSON output")

    compare_parser = sub.add_parser("compare", help="Compare all cached episode analyses")
    compare_parser.add_argument("--json", action="store_true", help="Print full JSON output")

    sub.add_parser("sources", help="List tracked channels")

    add_parser = sub.add_parser("add", help="Add a YouTube channel to track")
    add_parser.add_argument("channel_url", help="YouTube channel URL (e.g. https://www.youtube.com/@ChannelName)")

    dispatch = {
        "check": _cmd_check,
        "run": _cmd_run,
        "sources": _cmd_sources,
        "add": _cmd_add,
        "analyze": _cmd_analyze,
        "compare": _cmd_compare,
    }

    args = parser.parse_args()
    handler = dispatch.get(args.command)

    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
