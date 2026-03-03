"""Tests for mie.ingest.feed_monitor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import feedparser

from mie.ingest.feed_monitor import (
    ChannelConfig,
    _load_archive,
    _matches_keywords,
    fetch_feed,
    get_new_episodes,
    load_sources,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_FEED = FIXTURES_DIR / "sample_feed.xml"


# ── load_sources ─────────────────────────────────────────────────────────────


def test_load_sources(tmp_path: Path) -> None:
    """load_sources should parse a YAML file into ChannelConfig objects."""
    src = tmp_path / "sources.yaml"
    src.write_text(
        "channels:\n"
        '  - name: "Alpha"\n'
        '    channel_id: "UC_ALPHA"\n'
        "    keywords: []\n"
        "    enabled: true\n"
        '  - name: "Beta"\n'
        '    channel_id: "UC_BETA"\n'
        '    keywords: ["macro"]\n'
        "    enabled: false\n"
    )

    channels = load_sources(src)

    assert len(channels) == 1
    assert channels[0].name == "Alpha"
    assert channels[0].channel_id == "UC_ALPHA"


def test_load_sources_disabled_filtered_out(tmp_path: Path) -> None:
    """Disabled channels should not appear in the result."""
    src = tmp_path / "sources.yaml"
    src.write_text(
        "channels:\n"
        '  - name: "Off"\n'
        '    channel_id: "UC_OFF"\n'
        "    enabled: false\n"
    )

    assert load_sources(src) == []


# ── _load_archive ────────────────────────────────────────────────────────────


def test_load_archive_parses_ids(tmp_path: Path) -> None:
    """_load_archive should return video IDs from the yt-dlp archive."""
    archive = tmp_path / "archive.txt"
    archive.write_text("youtube abc123\nyoutube def456\n")

    ids = _load_archive(archive)

    assert ids == {"abc123", "def456"}


def test_load_archive_missing_file(tmp_path: Path) -> None:
    """_load_archive should return an empty set if the file doesn't exist."""
    assert _load_archive(tmp_path / "nonexistent.txt") == set()


# ── _matches_keywords ────────────────────────────────────────────────────────


def test_matches_keywords_empty_matches_all() -> None:
    assert _matches_keywords("Any Title Here", []) is True


def test_matches_keywords_case_insensitive() -> None:
    assert _matches_keywords("Forward Guidance Episode 10", ["forward guidance"]) is True


def test_matches_keywords_no_match() -> None:
    assert _matches_keywords("Weekly Crypto Roundup", ["forward guidance"]) is False


def test_matches_keywords_partial_match() -> None:
    assert _matches_keywords("Special Odd Lots Episode", ["odd lots"]) is True


# ── fetch_feed ───────────────────────────────────────────────────────────────


def test_fetch_feed_parses_xml() -> None:
    """fetch_feed should extract video entries from a YouTube Atom feed."""
    parsed = feedparser.parse(str(SAMPLE_FEED))

    with patch("mie.ingest.feed_monitor.feedparser.parse", return_value=parsed):
        entries = fetch_feed("UC_TEST_CHANNEL")

    assert len(entries) == 3
    assert entries[0]["video_id"] == "abc123"
    assert entries[0]["title"] == "Forward Guidance: Fed Rate Decision Deep Dive"
    assert entries[2]["video_id"] == "ghi789"


# ── get_new_episodes ─────────────────────────────────────────────────────────


def _make_parsed_feed() -> feedparser.FeedParserDict:
    return feedparser.parse(str(SAMPLE_FEED))


def test_get_new_episodes_returns_unarchived(tmp_path: Path) -> None:
    """get_new_episodes should skip videos already in the archive."""
    archive = tmp_path / "archive.txt"
    archive.write_text("youtube abc123\n")

    sources = [ChannelConfig(name="TestPod", channel_id="UC_TEST_CHANNEL")]

    with patch(
        "mie.ingest.feed_monitor.feedparser.parse",
        return_value=_make_parsed_feed(),
    ):
        episodes = get_new_episodes(sources=sources, archive_path=archive)

    video_ids = [ep.video_id for ep in episodes]
    assert "abc123" not in video_ids
    assert "def456" in video_ids
    assert "ghi789" in video_ids


def test_get_new_episodes_keyword_filter(tmp_path: Path) -> None:
    """get_new_episodes should filter by keywords when configured."""
    archive = tmp_path / "archive.txt"
    archive.write_text("")

    sources = [
        ChannelConfig(
            name="TestPod",
            channel_id="UC_TEST_CHANNEL",
            keywords=["forward guidance"],
        )
    ]

    with patch(
        "mie.ingest.feed_monitor.feedparser.parse",
        return_value=_make_parsed_feed(),
    ):
        episodes = get_new_episodes(sources=sources, archive_path=archive)

    titles = [ep.title for ep in episodes]
    assert len(episodes) == 2
    assert all("Forward Guidance" in t for t in titles)


def test_get_new_episodes_empty_archive(tmp_path: Path) -> None:
    """With no archive, all feed entries should be returned."""
    archive = tmp_path / "archive.txt"

    sources = [ChannelConfig(name="TestPod", channel_id="UC_TEST_CHANNEL")]

    with patch(
        "mie.ingest.feed_monitor.feedparser.parse",
        return_value=_make_parsed_feed(),
    ):
        episodes = get_new_episodes(sources=sources, archive_path=archive)

    assert len(episodes) == 3


def test_get_new_episodes_builds_correct_urls(tmp_path: Path) -> None:
    """Episode URLs should be valid YouTube watch links."""
    archive = tmp_path / "archive.txt"

    sources = [ChannelConfig(name="TestPod", channel_id="UC_TEST_CHANNEL")]

    with patch(
        "mie.ingest.feed_monitor.feedparser.parse",
        return_value=_make_parsed_feed(),
    ):
        episodes = get_new_episodes(sources=sources, archive_path=archive)

    for ep in episodes:
        assert ep.url.startswith("https://www.youtube.com/watch?v=")
        assert ep.video_id in ep.url
