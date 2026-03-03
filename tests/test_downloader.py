"""Tests for mie.ingest.downloader."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from mie.ingest.downloader import download_audio


@patch("mie.ingest.downloader.yt_dlp.YoutubeDL")
def test_download_audio_calls_yt_dlp(mock_ydl_class: MagicMock, tmp_path: Path) -> None:
    """download_audio should invoke yt-dlp with the given URL."""
    mock_ydl_instance = MagicMock()
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)

    url = "https://www.youtube.com/watch?v=test123"
    download_audio(url, output_dir=tmp_path, archive_path=tmp_path / "archive.txt")

    mock_ydl_instance.download.assert_called_once_with([url])


@patch("mie.ingest.downloader.yt_dlp.YoutubeDL")
def test_download_audio_creates_output_dir(
    mock_ydl_class: MagicMock, tmp_path: Path
) -> None:
    """download_audio should create the output directory if it doesn't exist."""
    mock_ydl_instance = MagicMock()
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)

    new_dir = tmp_path / "new_downloads"
    download_audio(
        "https://www.youtube.com/watch?v=abc",
        output_dir=new_dir,
        archive_path=tmp_path / "archive.txt",
    )

    assert new_dir.exists()


@patch("mie.ingest.downloader.yt_dlp.YoutubeDL")
def test_download_audio_uses_custom_codec_and_quality(
    mock_ydl_class: MagicMock, tmp_path: Path
) -> None:
    """download_audio should pass the codec and quality to yt-dlp options."""
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)

    download_audio(
        "https://www.youtube.com/watch?v=abc",
        output_dir=tmp_path,
        archive_path=tmp_path / "archive.txt",
        codec="wav",
        quality="320",
    )

    # Grab the options dict passed to YoutubeDL()
    call_args = mock_ydl_class.call_args
    opts = call_args[0][0] if call_args[0] else call_args[1]
    postprocessor = opts["postprocessors"][0]
    assert postprocessor["preferredcodec"] == "wav"
    assert postprocessor["preferredquality"] == "320"
