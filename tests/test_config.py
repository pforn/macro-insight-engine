"""Tests for mie.config."""

from pathlib import Path

from mie import config


def test_model_id_has_default() -> None:
    assert config.MODEL_ID == "gemini-2.5-flash"


def test_audio_defaults() -> None:
    assert config.AUDIO_CODEC == "mp3"
    assert config.AUDIO_QUALITY == "192"


def test_paths_are_pathlib_objects() -> None:
    assert isinstance(config.DOWNLOADS_DIR, Path)
    assert isinstance(config.OUTPUT_DIR, Path)
    assert isinstance(config.ARCHIVE_PATH, Path)


def test_project_root_is_repo_root() -> None:
    """PROJECT_ROOT should be the repo root (contains pyproject.toml)."""
    assert (config.PROJECT_ROOT / "pyproject.toml").exists()
