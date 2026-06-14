import time
from typing import Any

import requests

APEWISDOM_BASE = "https://apewisdom.io/api/v1.0/filter/{filter}/page/{page}"

DEFAULT_FILTER = "all-stocks"
MAX_PAGES = 5  # 500 results max per call


def get_top(n: int = 10, filter_name: str = DEFAULT_FILTER) -> list[dict[str, Any]]:
    """Return the top n tickers by current mentions from ApeWisdom."""
    try:
        resp = requests.get(
            APEWISDOM_BASE.format(filter=filter_name, page=1),
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except requests.RequestException as exc:
        raise RuntimeError(f"ApeWisdom API error: {exc}") from exc

    top = []
    for item in results[:n]:
        top.append({
            "ticker": (item.get("ticker") or "").upper(),
            "rank": item.get("rank"),
            "name": item.get("name", ""),
            "mention_count": int(item.get("mentions") or 0),
            "upvotes": int(item.get("upvotes") or 0),
            "rank_24h_ago": item.get("rank_24h_ago"),
            "mentions_24h_ago": int(item.get("mentions_24h_ago") or 0),
        })
    return top


def get_mentions(
    tickers: list[str],
    filter_name: str = DEFAULT_FILTER,
) -> dict[str, Any]:
    targets = {t.upper() for t in tickers}
    found: dict[str, Any] = {}

    for page in range(1, MAX_PAGES + 1):
        try:
            resp = requests.get(
                APEWISDOM_BASE.format(filter=filter_name, page=page),
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"ApeWisdom API error: {exc}") from exc

        for item in body.get("results", []):
            ticker = (item.get("ticker") or "").upper()
            if ticker in targets:
                found[ticker] = {
                    "rank": item.get("rank"),
                    "name": item.get("name", ticker),
                    "mention_count": int(item.get("mentions") or 0),
                    "upvotes": int(item.get("upvotes") or 0),
                    "rank_24h_ago": item.get("rank_24h_ago"),
                    "mentions_24h_ago": int(item.get("mentions_24h_ago") or 0),
                }

        total_pages = body.get("pages", 1)
        if page >= total_pages or len(found) == len(targets):
            break

        time.sleep(0.1)

    # fill in zeros for any tickers not found in rankings
    for ticker in tickers:
        if ticker.upper() not in found:
            found[ticker.upper()] = {
                "rank": None,
                "name": ticker,
                "mention_count": 0,
                "upvotes": 0,
                "rank_24h_ago": None,
                "mentions_24h_ago": 0,
            }

    return found
