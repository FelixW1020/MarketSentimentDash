import json
from typing import Any

import anthropic

import config

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


_NO_COVERAGE = {
    "summary": "No recent NYT coverage found for this ticker.",
    "sentiment": "Neutral",
    "rationale": "No articles to analyze.",
}


def summarize_articles(ticker: str, articles: list[dict[str, Any]]) -> dict[str, str]:
    if not articles:
        return _NO_COVERAGE

    snippets = []
    for a in articles[:10]:
        parts = [a["headline"]]
        if a.get("abstract"):
            parts.append(a["abstract"])
        snippets.append(" — ".join(parts))

    article_text = "\n".join(f"- {s}" for s in snippets)

    prompt = f"""You are a neutral financial news analyst. Below are recent New York Times headlines and abstracts about {ticker}.

{article_text}

Respond ONLY with a JSON object in this exact shape:
{{
  "summary": "<3-4 sentence plain-language summary of what the news says>",
  "sentiment": "<one of: Bullish | Neutral | Bearish>",
  "rationale": "<one sentence explaining the tone of coverage — NOT a buy/sell recommendation>"
}}

Do not include any text outside the JSON object."""

    client = _get_client()
    try:
        message = client.messages.create(
            model=config.MODEL_PRIMARY,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        return json.loads(raw)
    except (json.JSONDecodeError, KeyError, IndexError):
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            return {
                "summary": raw[:500] if raw else "Summary unavailable.",
                "sentiment": "Neutral",
                "rationale": "Could not parse structured response.",
            }
    except anthropic.APIError as exc:
        raise RuntimeError(f"Anthropic API error for {ticker}: {exc}") from exc
