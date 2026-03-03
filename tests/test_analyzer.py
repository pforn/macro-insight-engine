"""Tests for mie.processing.analyzer — structured two-pass inference."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mie.ingest.feed_monitor import Episode
from mie.schemas import (
    AgreementTopic,
    ComparisonReport,
    ControversyPosition,
    ControversyTopic,
    KeyClaim,
    PodcastAnalysis,
    TopicAnalysis,
    TopicSentiment,
    UniqueInsight,
)
from mie.processing.analyzer import (
    analyze_episode,
    compare_episodes,
    is_analyzed,
    load_cached_analyses,
    save_analysis,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_episode(video_id: str = "vid_001") -> Episode:
    return Episode(
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        title="Test Macro Podcast",
        channel_name="TestChannel",
        published="2026-02-28",
    )


def _make_analysis(
    episode_id: str = "vid_001", channel: str = "TestChannel"
) -> PodcastAnalysis:
    return PodcastAnalysis(
        episode_id=episode_id,
        title="Test Macro Podcast",
        channel=channel,
        published="2026-02-28",
        topics=[
            TopicAnalysis(
                topic="Fed Rates",
                summary="Discussed rate cuts.",
                sentiment="bearish",
                confidence="high",
            )
        ],
        key_claims=[
            KeyClaim(
                claim="Fed will cut 50bps in March.",
                speaker="Guest A",
                topic="Fed Rates",
                is_contrarian=False,
            )
        ],
        overall_sentiment="bearish",
        summary="A bearish macro outlook.",
    )


def _make_comparison_dict() -> dict:
    return ComparisonReport(
        period="2026-02-21 to 2026-02-28",
        episodes_analyzed=["vid_001", "vid_002"],
        consensus_topics=[
            AgreementTopic(
                topic="Fed Rates",
                shared_view="Rate cuts expected.",
                sentiment="bearish",
                supporting_episodes=["vid_001", "vid_002"],
            )
        ],
        controversial_topics=[
            ControversyTopic(
                topic="USD",
                positions=[
                    ControversyPosition(
                        episode_id="vid_001", stance="bearish", summary="Weak dollar."
                    ),
                    ControversyPosition(
                        episode_id="vid_002", stance="bullish", summary="Strong dollar."
                    ),
                ],
            )
        ],
        unique_insights=[
            UniqueInsight(
                episode_id="vid_001",
                channel="TestChannel",
                insight="Rare earths underpriced.",
                topic="Commodities",
            )
        ],
        overall_market_sentiment="mixed",
        sentiment_by_topic=[
            TopicSentiment(topic="Fed Rates", sentiment="bearish"),
        ],
    ).model_dump()


def _create_mp3(directory: Path, name: str = "test_episode.mp3") -> Path:
    path = directory / name
    path.write_bytes(b"\x00" * 100)
    return path


# ── Persistence ──────────────────────────────────────────────────────────────


def test_save_and_load_analysis(tmp_path: Path) -> None:
    analysis = _make_analysis()
    save_analysis(analysis, tmp_path)

    loaded = load_cached_analyses(tmp_path)
    assert len(loaded) == 1
    assert loaded[0] == analysis


def test_is_analyzed(tmp_path: Path) -> None:
    assert is_analyzed("vid_001", tmp_path) is False
    save_analysis(_make_analysis(), tmp_path)
    assert is_analyzed("vid_001", tmp_path) is True


def test_load_cached_analyses_skips_comparison_files(tmp_path: Path) -> None:
    save_analysis(_make_analysis("ep1"), tmp_path)
    (tmp_path / "comparison_2026.json").write_text("{}")

    loaded = load_cached_analyses(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].episode_id == "ep1"


def test_load_cached_analyses_empty_dir(tmp_path: Path) -> None:
    assert load_cached_analyses(tmp_path) == []


def test_load_cached_analyses_missing_dir(tmp_path: Path) -> None:
    assert load_cached_analyses(tmp_path / "nonexistent") == []


# ── Pass 1: analyze_episode ──────────────────────────────────────────────────


@patch("mie.processing.analyzer.gemini_client")
def test_analyze_episode_happy_path(mock_gc: MagicMock, tmp_path: Path) -> None:
    mp3 = _create_mp3(tmp_path)
    episode = _make_episode()

    mock_client = MagicMock()
    mock_gc.get_client.return_value = mock_client

    fake_file = MagicMock()
    fake_file.name = "files/uploaded_abc"
    fake_file.state = None
    mock_gc.upload_file.return_value = fake_file
    mock_gc.wait_for_processing.return_value = fake_file

    mock_gc.generate_structured.return_value = _make_analysis().model_dump()

    output_dir = tmp_path / "out"
    result = analyze_episode(mp3, episode, output_dir=output_dir)

    assert isinstance(result, PodcastAnalysis)
    assert result.episode_id == "vid_001"
    assert (output_dir / "vid_001.json").is_file()
    assert mp3.exists(), "Original file should be restored"


@patch("mie.processing.analyzer.gemini_client")
def test_analyze_episode_restores_filename_on_error(
    mock_gc: MagicMock, tmp_path: Path
) -> None:
    mp3 = _create_mp3(tmp_path)
    episode = _make_episode()

    mock_gc.get_client.return_value = MagicMock()
    mock_gc.upload_file.side_effect = RuntimeError("upload failed")

    with pytest.raises(RuntimeError, match="upload failed"):
        analyze_episode(mp3, episode, output_dir=tmp_path / "out")

    assert mp3.exists(), "Original file should be restored after error"


# ── Pass 2: compare_episodes ────────────────────────────────────────────────


@patch("mie.processing.analyzer.gemini_client")
def test_compare_episodes_happy_path(mock_gc: MagicMock, tmp_path: Path) -> None:
    a1 = _make_analysis("vid_001", "Channel A")
    a2 = _make_analysis("vid_002", "Channel B")

    mock_client = MagicMock()
    mock_gc.get_client.return_value = mock_client
    mock_gc.generate_structured.return_value = _make_comparison_dict()

    report = compare_episodes([a1, a2], output_dir=tmp_path)

    assert isinstance(report, ComparisonReport)
    assert len(report.episodes_analyzed) == 2
    mock_gc.generate_structured.assert_called_once()

    comparison_files = list(tmp_path.glob("comparison_*.json"))
    assert len(comparison_files) == 1


def test_compare_episodes_requires_two(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 2"):
        compare_episodes([_make_analysis()], output_dir=tmp_path)


def test_compare_episodes_requires_nonempty(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 2"):
        compare_episodes([], output_dir=tmp_path)
