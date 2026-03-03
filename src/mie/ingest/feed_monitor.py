"""YouTube RSS feed monitor for tracking new podcast episodes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import feedparser
import yaml

from mie.config import ARCHIVE_PATH, SOURCES_PATH

_YT_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
_YT_WATCH_URL = "https://www.youtube.com/watch?v={video_id}"

_REQUEST_DELAY_SECONDS = 1.5


@dataclass
class ChannelConfig:
    """A tracked YouTube channel from ``sources.yaml``."""

    name: str
    channel_id: str
    keywords: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class Episode:
    """A new episode discovered from an RSS feed."""

    video_id: str
    url: str
    title: str
    channel_name: str
    published: str


def load_sources(path: Path = SOURCES_PATH) -> list[ChannelConfig]:
    """Parse ``sources.yaml`` and return a list of channel configs.

    Only channels with ``enabled: true`` are returned.
    """
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f)

    channels: list[ChannelConfig] = []
    for entry in data.get("channels", []):
        cfg = ChannelConfig(
            name=entry["name"],
            channel_id=entry["channel_id"],
            keywords=entry.get("keywords", []),
            enabled=entry.get("enabled", True),
        )
        if cfg.enabled:
            channels.append(cfg)

    return channels


def fetch_feed(channel_id: str) -> list[dict[str, str]]:
    """Fetch a YouTube channel's Atom feed and return parsed entries.

    Each entry dict contains ``video_id``, ``title``, and ``published``.
    Returns an empty list on network/parse errors.
    """
    url = _YT_FEED_URL.format(channel_id=channel_id)
    feed = feedparser.parse(url)

    entries: list[dict[str, str]] = []
    for entry in feed.get("entries", []):
        video_id = entry.get("yt_videoid", "")
        if not video_id:
            link = entry.get("link", "")
            if "v=" in link:
                video_id = link.split("v=")[-1].split("&")[0]

        if video_id:
            entries.append(
                {
                    "video_id": video_id,
                    "title": entry.get("title", ""),
                    "published": entry.get("published", ""),
                }
            )

    return entries


def _load_archive(archive_path: Path) -> set[str]:
    """Read yt-dlp's archive file and return the set of downloaded video IDs.

    The archive format is ``youtube VIDEO_ID`` per line.
    """
    if not archive_path.exists():
        return set()

    ids: set[str] = set()
    with open(archive_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                ids.add(parts[1])
    return ids


def _matches_keywords(title: str, keywords: list[str]) -> bool:
    """Return True if *title* contains any of the *keywords* (case-insensitive).

    An empty keyword list matches everything.
    """
    if not keywords:
        return True
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


def get_new_episodes(
    sources: list[ChannelConfig] | None = None,
    archive_path: Path = ARCHIVE_PATH,
) -> list[Episode]:
    """Check all tracked channels and return episodes not yet downloaded.

    Fetches each channel's RSS feed, filters by keyword and archive state,
    and returns a list of :class:`Episode` objects ready for download.
    """
    if sources is None:
        sources = load_sources()

    archived_ids = _load_archive(archive_path)
    episodes: list[Episode] = []

    for i, channel in enumerate(sources):
        if i > 0:
            time.sleep(_REQUEST_DELAY_SECONDS)

        entries = fetch_feed(channel.channel_id)

        for entry in entries:
            vid = entry["video_id"]
            if vid in archived_ids:
                continue
            if not _matches_keywords(entry["title"], channel.keywords):
                continue

            episodes.append(
                Episode(
                    video_id=vid,
                    url=_YT_WATCH_URL.format(video_id=vid),
                    title=entry["title"],
                    channel_name=channel.name,
                    published=entry["published"],
                )
            )

    return episodes
