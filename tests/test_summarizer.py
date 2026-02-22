"""Tests for mie.processing.summarizer."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from mie.processing.summarizer import summarize_latest_audio


def _create_mp3(directory: Path, name: str = "test_episode.mp3") -> Path:
    """Create a dummy MP3 file for testing."""
    path = directory / name
    path.write_bytes(b"\x00" * 100)
    return path


def test_returns_none_when_no_mp3s(tmp_path: Path) -> None:
    result = summarize_latest_audio(directory=tmp_path)
    assert result is None


@patch("mie.processing.summarizer.gemini_client")
def test_summarize_returns_summary_text(mock_gc: MagicMock, tmp_path: Path) -> None:
    """Full happy-path: file found → uploaded → summarised → original name restored."""
    mp3 = _create_mp3(tmp_path)

    mock_client = MagicMock()
    mock_gc.get_client.return_value = mock_client

    fake_file = MagicMock()
    fake_file.name = "files/abc123"
    fake_file.state = None
    mock_gc.upload_file.return_value = fake_file
    mock_gc.wait_for_processing.return_value = fake_file
    mock_gc.generate_summary.return_value = "This is a test summary."

    result = summarize_latest_audio(directory=tmp_path)

    assert result == "This is a test summary."
    mock_gc.upload_file.assert_called_once()
    mock_gc.generate_summary.assert_called_once()

    # Original filename should be restored
    assert mp3.exists()
    assert not (tmp_path / "temp_processing.mp3").exists()


@patch("mie.processing.summarizer.gemini_client")
def test_original_filename_restored_on_error(
    mock_gc: MagicMock, tmp_path: Path
) -> None:
    """If Gemini fails, the original filename must still be restored."""
    mp3 = _create_mp3(tmp_path)

    mock_gc.get_client.return_value = MagicMock()
    mock_gc.upload_file.side_effect = RuntimeError("upload boom")

    result = summarize_latest_audio(directory=tmp_path)

    assert result is None
    # The original file should be restored despite the error
    assert mp3.exists()
