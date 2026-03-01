"""Two-pass structured podcast analysis.

Pass 1 — ``analyze_episode``:  Upload audio to Gemini and extract a
    structured ``PodcastAnalysis`` (topics, claims, sentiment).

Pass 2 — ``compare_episodes``:  Take cached per-episode analyses and
    produce a ``ComparisonReport`` (agreement, controversy, unique insights).

All Gemini I/O is delegated to :mod:`mie.processing.gemini_client`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mie.config import GEMINI_API_KEY, MODEL_ID, OUTPUT_DIR
from mie.ingest.feed_monitor import Episode
from mie.schemas import ComparisonReport, PodcastAnalysis
from mie.processing import gemini_client
from mie.prompts import COMPARISON_SYSTEM_PROMPT, EXTRACTION_SYSTEM_PROMPT

ANALYSIS_DIR: Path = OUTPUT_DIR / "analyses"


# ── Persistence helpers ────────────────────────────────────────────────────


def _analysis_path(episode_id: str, output_dir: Path = ANALYSIS_DIR) -> Path:
    return output_dir / f"{episode_id}.json"


def save_analysis(analysis: PodcastAnalysis, output_dir: Path = ANALYSIS_DIR) -> Path:
    """Serialize a ``PodcastAnalysis`` to JSON on disk.  Returns the file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = _analysis_path(analysis.episode_id, output_dir)
    path.write_text(analysis.model_dump_json(indent=2))
    return path


def load_cached_analyses(output_dir: Path = ANALYSIS_DIR) -> list[PodcastAnalysis]:
    """Load all cached ``PodcastAnalysis`` JSON files from *output_dir*."""
    if not output_dir.is_dir():
        return []
    analyses: list[PodcastAnalysis] = []
    for p in sorted(output_dir.glob("*.json")):
        if p.name.startswith("comparison_"):
            continue
        analyses.append(PodcastAnalysis.model_validate_json(p.read_text()))
    return analyses


def is_analyzed(episode_id: str, output_dir: Path = ANALYSIS_DIR) -> bool:
    """Return True if a cached analysis already exists for *episode_id*."""
    return _analysis_path(episode_id, output_dir).is_file()


# ── Pass 1: Per-episode extraction ─────────────────────────────────────────


def analyze_episode(
    audio_path: Path,
    episode: Episode,
    output_dir: Path = ANALYSIS_DIR,
) -> PodcastAnalysis:
    """Upload *audio_path* to Gemini and extract a structured analysis.

    The result is validated against :class:`PodcastAnalysis`, persisted as
    JSON, and returned.
    """
    safe_name = f"temp_analysis{audio_path.suffix}"
    safe_path = audio_path.parent / safe_name
    os.rename(audio_path, safe_path)

    try:
        client = gemini_client.get_client(GEMINI_API_KEY)

        print(f"  Uploading {audio_path.name}...")
        uploaded = gemini_client.upload_file(client, str(safe_path))
        uploaded = gemini_client.wait_for_processing(client, uploaded)

        user_prompt = (
            f"Analyze this podcast episode.\n"
            f"Episode ID: {episode.video_id}\n"
            f"Title: {episode.title}\n"
            f"Channel: {episode.channel_name}\n"
            f"Published: {episode.published}\n"
        )

        print("  Extracting structured analysis...")
        raw = gemini_client.generate_structured(
            client=client,
            model=MODEL_ID,
            content=uploaded,
            user_prompt=user_prompt,
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            response_schema=PodcastAnalysis,
        )

        analysis = PodcastAnalysis.model_validate(raw)
        path = save_analysis(analysis, output_dir)
        print(f"  Saved analysis -> {path}")
        return analysis

    finally:
        if safe_path.exists():
            os.rename(safe_path, audio_path)


# ── Pass 2: Cross-podcast comparison ───────────────────────────────────────


def compare_episodes(
    analyses: list[PodcastAnalysis] | None = None,
    output_dir: Path = ANALYSIS_DIR,
) -> ComparisonReport:
    """Compare multiple episode analyses and produce a ``ComparisonReport``.

    If *analyses* is ``None``, loads all cached analyses from *output_dir*.
    The comparison is performed via Gemini structured output (no audio upload
    required — only the JSON data is sent as context).
    """
    if analyses is None:
        analyses = load_cached_analyses(output_dir)

    if len(analyses) < 2:
        raise ValueError(
            f"Need at least 2 episode analyses to compare, got {len(analyses)}."
        )

    analyses_json = [a.model_dump() for a in analyses]
    episodes_summary = ", ".join(
        f"{a.channel} — {a.title}" for a in analyses
    )

    dates = sorted(a.published for a in analyses if a.published)
    period = f"{dates[0]} to {dates[-1]}" if len(dates) >= 2 else "unknown"

    user_prompt = (
        f"Compare the following {len(analyses)} podcast episode analyses.\n"
        f"Period: {period}\n"
        f"Episodes: {episodes_summary}\n\n"
        f"Episode analyses (JSON):\n{json.dumps(analyses_json, indent=2)}"
    )

    client = gemini_client.get_client(GEMINI_API_KEY)

    print("Generating cross-podcast comparison...")
    raw = gemini_client.generate_structured(
        client=client,
        model=MODEL_ID,
        content=user_prompt,
        user_prompt="Produce the comparison report.",
        system_prompt=COMPARISON_SYSTEM_PROMPT,
        response_schema=ComparisonReport,
    )

    report = ComparisonReport.model_validate(raw)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"comparison_{period.replace(' ', '_')}.json"
    report_path.write_text(report.model_dump_json(indent=2))
    print(f"Saved comparison -> {report_path}")

    return report
