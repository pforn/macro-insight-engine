"""Pass 3: Portfolio risk assessment based on market insights."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from mie.config import GEMINI_API_KEY, MODEL_ID, POSITIONS_PATH
from mie.processing import gemini_client
from mie.prompts import RISK_ASSESSMENT_SYSTEM_PROMPT
from mie.schemas import ComparisonReport, PortfolioRiskReport, Position


def load_positions(path: Path = POSITIONS_PATH) -> list[Position]:
    """Load user positions from a YAML file."""
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "trades" not in data:
        return []

    return [Position(**p) for p in data["trades"]]


def assess_portfolio_risk(
    report: ComparisonReport,
    positions: list[Position] | None = None,
    output_dir: Path | None = None,
) -> PortfolioRiskReport:
    """Assess the risk of user positions against the provided market comparison report.

    If *positions* is None, loads from the default `positions.yaml`.
    If *output_dir* is provided, saves the report as JSON.
    """
    if positions is None:
        positions = load_positions()

    if not positions:
        # Return an empty report if no positions are defined
        return PortfolioRiskReport(
            positions_analyzed=0,
            risks=[],
            overall_portfolio_risk="Low",
            summary="No positions defined for analysis.",
        )

    # Prepare context for the model
    positions_summary = "\n".join(
        f"- {p.ticker} ({p.type}): {p.thesis}" for p in positions
    )

    user_prompt = (
        f"Assess the risk for the following portfolio based on the market report.\n\n"
        f"MARKET REPORT (JSON):\n{report.model_dump_json(indent=2)}\n\n"
        f"USER POSITIONS:\n{positions_summary}\n"
    )

    client = gemini_client.get_client(GEMINI_API_KEY)

    print("Generating portfolio risk assessment...")
    raw = gemini_client.generate_structured(
        client=client,
        model=MODEL_ID,
        content=user_prompt,
        user_prompt="Produce the risk assessment report.",
        system_prompt=RISK_ASSESSMENT_SYSTEM_PROMPT,
        response_schema=PortfolioRiskReport,
    )

    risk_report = PortfolioRiskReport.model_validate(raw)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"risk_assessment_{report.period.replace(' ', '_')}.json"
        report_path.write_text(risk_report.model_dump_json(indent=2))
        print(f"Saved risk assessment -> {report_path}")

    return risk_report
