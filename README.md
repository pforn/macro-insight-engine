# 🤖 Macro Insight Engine (MIE)

An automated pipeline to synthesize global macro sentiment from leading financial podcasts.

## 📌 Project Overview

The **Macro Insight Engine** is a data engineering project that automates the collection and synthesis of unstructured audio data from elite finance podcasts (e.g., *Odd Lots*, *The Market Huddle*, *Macro Voices*). It leverages **Gemini 1.5 Pro** to identify market "consensus" vs. "divergence" in the Forex and Bond markets, providing a weekly actionable summary for traders.

## 🎯 The Problem

Macro traders face "Information Overload." Listening to 10+ hours of professional podcasts weekly is unsustainable. MIE reduces 10 hours of audio to a 5-minute technical brief, highlighting specific trade risks and conflicting expert takes.

## 🏗️ Architecture

The pipeline is built on a modular "Ingest-Process-Distill" architecture:

1.  **Ingest**: The `mie` CLI (using `yt-dlp`) monitors a `sources.yaml` registry for new episodes from YouTube channels.
2.  **Process**: Audio is uploaded to Gemini 1.5 Pro (2M token context window) for structured extraction of topics, claims, and sentiment.
3.  **Distill**: A second pass compares multiple episode analyses to identify:
    *   **Consensus**: Shared views on Fed policy and rates.
    *   **Divergence**: Conflicting takes on FX (e.g., USD direction).
    *   **Outliers**: Radical "tail risk" theories.
4.  **Action**: The engine maps these insights against a user-defined `positions.yaml` to flag specific trade risks.

## 🛠️ Tech Stack

*   **Language**: Python 3.12+
*   **Orchestration**: GitHub Actions (Cron-scheduled every Monday 08:00 AM UTC)
*   **AI Model**: Google Gemini 1.5 Pro / 2.5 Flash
*   **Data Handling**: Pydantic for schema validation, YAML for configuration.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/pforn/macro-insight-engine.git
cd macro-insight-engine

# Install dependencies (using uv or pip)
pip install -e .
```

### 2. Configuration

Create a `.env` file with your Gemini API key:

```bash
GEMINI_API_KEY=your_api_key_here
```

### 3. Manage Sources

Add YouTube channels to track:

```bash
mie add https://www.youtube.com/@OddLots
mie add https://www.youtube.com/@MacroVoices
```

This updates `sources.yaml`.

### 4. Define Your Positions

Create or edit `positions.yaml` to track your market exposure:

```yaml
trades:
  - ticker: "TLT"
    type: "Long"
    thesis: "Rates peaking in Q1"
  - ticker: "USD/JPY"
    type: "Short"
    thesis: "BOJ policy shift"
```

### 5. Run the Engine

Run the full pipeline (check feeds, download, analyze, compare):

```bash
mie run
```

Or run specific steps:

```bash
# Check for new episodes without downloading
mie check

# Assess risk for your portfolio based on cached analyses
mie risk
```

## 📊 Sample Output: "The Weekly Divergence"

| Topic | The Market Huddle Take | Odd Lots Take | Sentiment |
| :--- | :--- | :--- | :--- |
| **US 10YR Yield** | Target 4.5% (Bearish) | Neutral / Data Dependent | ⚠️ Divergence |
| **JPY** | Carry trade unwinding | Continued weakness | ⚠️ High Conflict |
| **Fed Policy** | Pause through Q3 | Cut in Q2 | 🟢 Consensus (Pause) |

## 👨‍💻 Author

Peter Fornasiero
