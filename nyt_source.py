import time
from typing import Any

import requests

import config

TICKER_TO_COMPANY: dict[str, str] = {
    "GME": "GameStop",
    "AMC": "AMC Entertainment",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "META": "Meta",
    "PLTR": "Palantir",
    "RIVN": "Rivian",
    "HOOD": "Robinhood",
    "SOFI": "SoFi",
    "BB": "BlackBerry",
    "NOK": "Nokia",
    "BBBY": "Bed Bath Beyond",
    "SPCE": "Virgin Galactic",
    "COIN": "Coinbase",
}

NYT_BASE = "https://api.nytimes.com/svc/search/v2/articlesearch.json"


def get_articles(
    ticker: str,
    lookback_days: int = 7,
    page_limit: int = 2,
) -> list[dict[str, Any]]:
    company = TICKER_TO_COMPANY.get(ticker.upper(), ticker)
    query = f"{company} {ticker}" if company != ticker else ticker

    articles: list[dict[str, Any]] = []
    for page in range(page_limit):
        try:
            resp = requests.get(
                NYT_BASE,
                params={
                    "q": query,
                    "sort": "newest",
                    "page": page,
                    "api-key": config.NYT_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            docs = resp.json().get("response", {}).get("docs", [])
            for doc in docs:
                articles.append(
                    {
                        "headline": doc.get("headline", {}).get("main", ""),
                        "abstract": doc.get("abstract", ""),
                        "url": doc.get("web_url", ""),
                        "pub_date": doc.get("pub_date", ""),
                        "byline": doc.get("byline", {}).get("original", ""),
                    }
                )
        except requests.RequestException as exc:
            raise RuntimeError(f"NYT API error for {ticker}: {exc}") from exc

        time.sleep(0.25)

    return articles
