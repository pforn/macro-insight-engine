"""Tests for mie.processing.risk_analyzer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from mie.processing.risk_analyzer import assess_portfolio_risk, load_positions
from mie.schemas import ComparisonReport, PortfolioRiskReport, Position


def test_load_positions(tmp_path: Path) -> None:
    path = tmp_path / "positions.yaml"
    path.write_text(
        """
trades:
  - ticker: "TLT"
    type: "Long"
    thesis: "Rates peaking"
"""
    )

    positions = load_positions(path)
    assert len(positions) == 1
    assert positions[0].ticker == "TLT"
    assert positions[0].type == "Long"


def test_load_positions_empty(tmp_path: Path) -> None:
    path = tmp_path / "positions.yaml"
    path.write_text("")
    assert load_positions(path) == []


def test_load_positions_missing(tmp_path: Path) -> None:
    assert load_positions(tmp_path / "missing.yaml") == []


@patch("mie.processing.risk_analyzer.gemini_client")
def test_assess_portfolio_risk(mock_gc: MagicMock, tmp_path: Path) -> None:
    report = ComparisonReport(
        period="2026-01-01 to 2026-01-07",
        episodes_analyzed=["ep1", "ep2"],
        consensus_topics=[],
        controversial_topics=[],
        unique_insights=[],
        overall_market_sentiment="mixed",
        sentiment_by_topic=[],
    )

    positions = [
        Position(ticker="TLT", type="Long", thesis="Rates peaking"),
    ]

    mock_client = MagicMock()
    mock_gc.get_client.return_value = mock_client
    mock_gc.generate_structured.return_value = {
        "positions_analyzed": 1,
        "risks": [
            {
                "ticker": "TLT",
                "risk_level": "Medium",
                "reasoning": "Mixed signals on rates.",
                "relevant_topics": ["Fed Policy"],
                "conflicting_insights": ["Fed might hike."],
            }
        ],
        "overall_portfolio_risk": "Medium",
        "summary": "Moderate risk due to rate uncertainty.",
    }

    risk_report = assess_portfolio_risk(report, positions, output_dir=tmp_path)

    assert isinstance(risk_report, PortfolioRiskReport)
    assert risk_report.positions_analyzed == 1
    assert risk_report.risks[0].ticker == "TLT"
    assert (tmp_path / "risk_assessment_2026-01-01_to_2026-01-07.json").exists()


def test_assess_portfolio_risk_no_positions() -> None:
    report = ComparisonReport(
        period="2026-01-01 to 2026-01-07",
        episodes_analyzed=[],
        consensus_topics=[],
        controversial_topics=[],
        unique_insights=[],
        overall_market_sentiment="mixed",
        sentiment_by_topic=[],
    )
    
    # Pass empty list explicitly
    risk_report = assess_portfolio_risk(report, positions=[])
    
    assert risk_report.positions_analyzed == 0
    assert risk_report.overall_portfolio_risk == "Low"
