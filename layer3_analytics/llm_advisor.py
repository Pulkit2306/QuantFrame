"""
LLM-powered strategy advisor using the Anthropic API with prompt caching.

Given backtest results and market metrics, the advisor suggests parameter
adjustments and flags anomalies. Prompt caching keeps costs low when
repeatedly querying with the same system context.
"""

import os
import json
import anthropic

SYSTEM_PROMPT = """You are a quantitative trading strategy advisor embedded in
QuantFrame, an algorithmic trading backtesting system. You analyze backtest
results and market performance metrics to provide concise, actionable insights.

Your responses must be valid JSON with this structure:
{
  "summary": "1-2 sentence overall assessment",
  "anomalies": ["list of detected anomalies or risks"],
  "parameter_suggestions": [
    {"parameter": "name", "current": val, "suggested": val, "reason": "why"}
  ],
  "regime": "trending | mean_reverting | choppy | unknown",
  "confidence": 0.0-1.0
}

Be direct and quantitative. Reference specific numbers from the data provided."""


def analyze_backtest(
    backtest_result: dict,
    market_metrics: dict,
    strategy_params: dict,
) -> dict:
    """
    Call Claude to analyze a backtest result and suggest improvements.
    Uses prompt caching on the system prompt to reduce API costs.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    user_message = f"""Analyze this backtest and market data:

BACKTEST RESULT:
{json.dumps(backtest_result, indent=2)}

MARKET METRICS:
{json.dumps(market_metrics, indent=2)}

CURRENT STRATEGY PARAMETERS:
{json.dumps(strategy_params, indent=2)}

Provide parameter tuning suggestions and flag any anomalies."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # cache the system prompt
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw, "error": "Could not parse JSON response"}


def detect_anomalies(metrics_list: list[dict]) -> list[dict]:
    """
    Use the LLM to scan a list of symbol metrics for anomalies
    (unusual drawdowns, vol spikes, etc.).
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    user_message = f"""Scan these market metrics for anomalies:

{json.dumps(metrics_list, indent=2)}

Return JSON array of anomalies: [{{"symbol": ..., "type": ..., "severity": "low|medium|high", "detail": ...}}]
Return empty array [] if no anomalies."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"error": "parse failure", "raw": raw}]
