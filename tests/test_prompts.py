"""Tests for mie.prompts — prompt registry and content validation.

These tests ensure every prompt is discoverable via the registry, is non-empty,
and that the registry stays in sync with the module-level constants.  They also
serve as a harness for experimenting with prompt variants: duplicate a test,
swap the prompt text, and assert on model output shape.
"""

from __future__ import annotations

import pytest

from mie.prompts import (
    COMPARISON_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    PROMPT_REGISTRY,
    RISK_ASSESSMENT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    get_prompt,
    list_prompts,
)

EXPECTED_PROMPTS = [
    "SYSTEM_PROMPT",
    "EXTRACTION_SYSTEM_PROMPT",
    "COMPARISON_SYSTEM_PROMPT",
    "RISK_ASSESSMENT_SYSTEM_PROMPT",
]


# ── Registry completeness ──────────────────────────────────────────────────


def test_list_prompts_returns_all() -> None:
    names = list_prompts()
    for expected in EXPECTED_PROMPTS:
        assert expected in names


def test_registry_matches_module_constants() -> None:
    assert PROMPT_REGISTRY["SYSTEM_PROMPT"] is SYSTEM_PROMPT
    assert PROMPT_REGISTRY["EXTRACTION_SYSTEM_PROMPT"] is EXTRACTION_SYSTEM_PROMPT
    assert PROMPT_REGISTRY["COMPARISON_SYSTEM_PROMPT"] is COMPARISON_SYSTEM_PROMPT
    assert PROMPT_REGISTRY["RISK_ASSESSMENT_SYSTEM_PROMPT"] is RISK_ASSESSMENT_SYSTEM_PROMPT


# ── get_prompt ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", EXPECTED_PROMPTS)
def test_get_prompt_returns_string(name: str) -> None:
    prompt = get_prompt(name)
    assert isinstance(prompt, str)
    assert len(prompt) > 50, f"{name} looks suspiciously short"


def test_get_prompt_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_prompt("NONEXISTENT_PROMPT")


# ── Prompt content sanity checks ───────────────────────────────────────────


@pytest.mark.parametrize("name", EXPECTED_PROMPTS)
def test_prompts_are_non_empty_and_trimmed(name: str) -> None:
    prompt = get_prompt(name)
    assert prompt == prompt.strip(), f"{name} has leading/trailing whitespace"
    assert len(prompt.split()) > 20, f"{name} is too short to be a useful system prompt"


def test_extraction_prompt_mentions_key_concepts() -> None:
    p = get_prompt("EXTRACTION_SYSTEM_PROMPT")
    assert "topic" in p.lower()
    assert "sentiment" in p.lower()
    assert "claim" in p.lower()


def test_comparison_prompt_mentions_key_concepts() -> None:
    p = get_prompt("COMPARISON_SYSTEM_PROMPT")
    assert "consensus" in p.lower()
    assert "controversy" in p.lower() or "conflicting" in p.lower()
    assert "unique" in p.lower()


def test_risk_prompt_mentions_key_concepts() -> None:
    p = get_prompt("RISK_ASSESSMENT_SYSTEM_PROMPT")
    assert "risk" in p.lower()
    assert "position" in p.lower()
    assert "high" in p.lower()
    assert "medium" in p.lower()
    assert "low" in p.lower()


# ── Pipeline ordering helper ───────────────────────────────────────────────

PIPELINE_STAGES = [
    ("Stage 0", "SYSTEM_PROMPT"),
    ("Stage 1", "EXTRACTION_SYSTEM_PROMPT"),
    ("Stage 2", "COMPARISON_SYSTEM_PROMPT"),
    ("Stage 3", "RISK_ASSESSMENT_SYSTEM_PROMPT"),
]


@pytest.mark.parametrize("stage_label,prompt_name", PIPELINE_STAGES)
def test_pipeline_stage_prompt_exists(stage_label: str, prompt_name: str) -> None:
    """Every pipeline stage has a registered prompt."""
    assert prompt_name in PROMPT_REGISTRY, f"{stage_label} prompt {prompt_name!r} missing"
