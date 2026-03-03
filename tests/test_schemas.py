"""Tests for mie.models — Pydantic schema validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mie.schemas import (
    AgreementTopic,
    ComparisonReport,
    ControversyPosition,
    ControversyTopic,
    KeyClaim,
    PodcastAnalysis,
    PortfolioRiskReport,
    Position,
    RiskAssessment,
    TopicAnalysis,
    TopicSentiment,
    UniqueInsight,
)


# ── TopicAnalysis ────────────────────────────────────────────────────────────


def test_topic_analysis_valid() -> None:
    t = TopicAnalysis(
        topic="Fed Rate Path",
        summary="Experts expect 75bps of cuts in 2026.",
        sentiment="bearish",
        confidence="high",
    )
    assert t.topic == "Fed Rate Path"
    assert t.sentiment == "bearish"


def test_topic_analysis_invalid_sentiment() -> None:
    with pytest.raises(ValidationError):
        TopicAnalysis(
            topic="X",
            summary="Y",
            sentiment="optimistic",  # type: ignore[arg-type]
            confidence="high",
        )


def test_topic_analysis_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        TopicAnalysis(
            topic="X",
            summary="Y",
            sentiment="neutral",
            confidence="very high",  # type: ignore[arg-type]
        )


# ── KeyClaim ─────────────────────────────────────────────────────────────────


def test_key_claim_contrarian_flag() -> None:
    claim = KeyClaim(
        claim="Gold will hit $5000 by Q3",
        speaker="Peter Schiff",
        topic="Gold Outlook",
        is_contrarian=True,
    )
    assert claim.is_contrarian is True


# ── PodcastAnalysis ──────────────────────────────────────────────────────────


def _make_podcast_analysis(**overrides: object) -> PodcastAnalysis:
    defaults = {
        "episode_id": "abc123",
        "title": "Test Episode",
        "channel": "TestPod",
        "published": "2026-02-28",
        "topics": [
            TopicAnalysis(
                topic="Fed Rates",
                summary="Discussion of rate path.",
                sentiment="bearish",
                confidence="high",
            )
        ],
        "key_claims": [
            KeyClaim(
                claim="Fed will cut 50bps in March.",
                speaker="Host",
                topic="Fed Rates",
                is_contrarian=False,
            )
        ],
        "overall_sentiment": "bearish",
        "summary": "A bearish take on rates.",
    }
    defaults.update(overrides)
    return PodcastAnalysis(**defaults)  # type: ignore[arg-type]


def test_podcast_analysis_roundtrip_json() -> None:
    analysis = _make_podcast_analysis()
    json_str = analysis.model_dump_json()
    restored = PodcastAnalysis.model_validate_json(json_str)
    assert restored == analysis


def test_podcast_analysis_invalid_overall_sentiment() -> None:
    with pytest.raises(ValidationError):
        _make_podcast_analysis(overall_sentiment="positive")


# ── ComparisonReport ─────────────────────────────────────────────────────────


def _make_comparison_report() -> ComparisonReport:
    return ComparisonReport(
        period="2026-02-21 to 2026-02-28",
        episodes_analyzed=["abc123", "def456"],
        consensus_topics=[
            AgreementTopic(
                topic="Fed Rate Path",
                shared_view="75bps of cuts expected.",
                sentiment="bearish",
                supporting_episodes=["abc123", "def456"],
            )
        ],
        controversial_topics=[
            ControversyTopic(
                topic="USD Outlook",
                positions=[
                    ControversyPosition(
                        episode_id="abc123",
                        stance="bearish",
                        summary="Dollar weakness ahead.",
                    ),
                    ControversyPosition(
                        episode_id="def456",
                        stance="bullish",
                        summary="Dollar strength persists.",
                    ),
                ],
            )
        ],
        unique_insights=[
            UniqueInsight(
                episode_id="abc123",
                channel="TestPod",
                insight="Rare earth supply crunch is underpriced.",
                topic="Commodities",
            )
        ],
        overall_market_sentiment="mixed",
        sentiment_by_topic=[
            TopicSentiment(topic="Fed Rate Path", sentiment="bearish"),
        ],
    )


def test_comparison_report_roundtrip_json() -> None:
    report = _make_comparison_report()
    json_str = report.model_dump_json()
    restored = ComparisonReport.model_validate_json(json_str)
    assert restored == report


def test_comparison_report_requires_episodes() -> None:
    report = _make_comparison_report()
    assert len(report.episodes_analyzed) == 2


# ── Position ─────────────────────────────────────────────────────────────────


def test_position_valid() -> None:
    p = Position(ticker="TLT", type="Long", thesis="Rates peaking")
    assert p.ticker == "TLT"
    assert p.type == "Long"


def test_position_invalid_type() -> None:
    with pytest.raises(ValidationError):
        Position(ticker="TLT", type="Flat", thesis="Neutral")  # type: ignore[arg-type]


# ── RiskAssessment ───────────────────────────────────────────────────────────


def test_risk_assessment_valid() -> None:
    r = RiskAssessment(
        ticker="TLT",
        risk_level="High",
        reasoning="Consensus is bearish on bonds.",
        relevant_topics=["Fed Rates"],
        conflicting_insights=["Fed will hike."],
    )
    assert r.risk_level == "High"
    assert len(r.relevant_topics) == 1


def test_risk_assessment_invalid_risk_level() -> None:
    with pytest.raises(ValidationError):
        RiskAssessment(
            ticker="TLT",
            risk_level="Extreme",  # type: ignore[arg-type]
            reasoning="Bad",
            relevant_topics=[],
            conflicting_insights=[],
        )


# ── PortfolioRiskReport ─────────────────────────────────────────────────────


def test_portfolio_risk_report_roundtrip_json() -> None:
    report = PortfolioRiskReport(
        positions_analyzed=1,
        risks=[
            RiskAssessment(
                ticker="USD/JPY",
                risk_level="Medium",
                reasoning="Mixed signals.",
                relevant_topics=["JPY", "Fed Policy"],
                conflicting_insights=["BOJ may tighten."],
            )
        ],
        overall_portfolio_risk="Medium",
        summary="Moderate risk.",
    )
    json_str = report.model_dump_json()
    restored = PortfolioRiskReport.model_validate_json(json_str)
    assert restored == report


def test_portfolio_risk_report_invalid_overall_risk() -> None:
    with pytest.raises(ValidationError):
        PortfolioRiskReport(
            positions_analyzed=0,
            risks=[],
            overall_portfolio_risk="Critical",  # type: ignore[arg-type]
            summary="Bad",
        )
