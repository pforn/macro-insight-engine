"""Pydantic schemas for structured podcast inference output.

Pass 1 models (per-podcast extraction):
    TopicAnalysis, KeyClaim, PodcastAnalysis

Pass 2 models (cross-podcast comparison):
    ControversyPosition, AgreementTopic, ControversyTopic,
    UniqueInsight, TopicSentiment, ComparisonReport

Pass 3 models (portfolio risk assessment):
    Position, RiskAssessment, PortfolioRiskReport
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

SentimentType = Literal["bullish", "bearish", "neutral", "mixed"]
ConfidenceType = Literal["high", "medium", "low"]
RiskLevel = Literal["High", "Medium", "Low"]


# ── Pass 1: Per-podcast extraction ──────────────────────────────────────────


class TopicAnalysis(BaseModel):
    """A single topic discussed in the podcast with sentiment."""

    topic: str
    summary: str
    sentiment: SentimentType
    confidence: ConfidenceType


class KeyClaim(BaseModel):
    """A specific factual assertion or prediction made during the episode."""

    claim: str
    speaker: str
    topic: str
    is_contrarian: bool


class PodcastAnalysis(BaseModel):
    """Structured extraction from a single podcast episode."""

    episode_id: str
    title: str
    channel: str
    published: str
    topics: list[TopicAnalysis]
    key_claims: list[KeyClaim]
    overall_sentiment: SentimentType
    summary: str


# ── Pass 2: Cross-podcast comparison ───────────────────────────────────────


class ControversyPosition(BaseModel):
    """One side of a controversial topic, tied to a specific episode."""

    episode_id: str
    stance: str
    summary: str


class AgreementTopic(BaseModel):
    """A topic where multiple podcasts share the same view."""

    topic: str
    shared_view: str
    sentiment: SentimentType
    supporting_episodes: list[str]


class ControversyTopic(BaseModel):
    """A topic where podcasts hold conflicting positions."""

    topic: str
    positions: list[ControversyPosition]


class UniqueInsight(BaseModel):
    """An insight that only appeared in a single episode."""

    episode_id: str
    channel: str
    insight: str
    topic: str


class TopicSentiment(BaseModel):
    """Aggregated sentiment for a single topic across all episodes."""

    topic: str
    sentiment: SentimentType


class ComparisonReport(BaseModel):
    """Cross-podcast comparison report generated from cached analyses."""

    period: str
    episodes_analyzed: list[str]
    consensus_topics: list[AgreementTopic]
    controversial_topics: list[ControversyTopic]
    unique_insights: list[UniqueInsight]
    overall_market_sentiment: SentimentType
    sentiment_by_topic: list[TopicSentiment]


# ── Pass 3: Portfolio Risk Assessment ──────────────────────────────────────

class Position(BaseModel):
    """A user-defined market position."""
    
    ticker: str
    type: Literal["Long", "Short"]
    thesis: str


class RiskAssessment(BaseModel):
    """Risk assessment for a specific position based on market insights."""
    
    ticker: str
    risk_level: RiskLevel
    reasoning: str
    relevant_topics: list[str]
    conflicting_insights: list[str]


class PortfolioRiskReport(BaseModel):
    """Overall risk report for the user's portfolio."""
    
    positions_analyzed: int
    risks: list[RiskAssessment]
    overall_portfolio_risk: RiskLevel
    summary: str
