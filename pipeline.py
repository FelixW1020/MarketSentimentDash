import hashlib
import json
from typing import Any, Optional

import config
import store
from apewisdom_source import get_top, get_mentions
from nyt_source import get_articles
from summarize import summarize_articles


def _cache_key(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"


def run(tickers: Optional[list] = None) -> dict[str, Any]:
    store.init_db()

    # If no tickers specified, fetch live top-N from ApeWisdom
    if tickers:
        fixed = [t.upper() for t in tickers]
        top_key = _cache_key("apewisdom", {"tickers": fixed})
        ape_rows = store.cache_get(top_key, config.CACHE_TTL_SECONDS)
        if ape_rows is None:
            raw = get_mentions(fixed, filter_name=config.APE_FILTER)
            ape_rows = [raw[t] | {"ticker": t} for t in fixed if t in raw]
            store.cache_set(top_key, ape_rows)
    else:
        top_key = _cache_key("ape_top", {"n": config.TOP_N, "filter": config.APE_FILTER})
        ape_rows = store.cache_get(top_key, config.CACHE_TTL_SECONDS)
        if ape_rows is None:
            ape_rows = get_top(config.TOP_N, config.APE_FILTER)
            store.cache_set(top_key, ape_rows)

    result: dict[str, Any] = {}
    for row in ape_rows:
        ticker = row["ticker"]
        if not ticker:
            continue

        nyt_key = _cache_key("nyt", {"ticker": ticker})
        articles = store.cache_get(nyt_key, config.CACHE_TTL_SECONDS)
        if articles is None:
            try:
                articles = get_articles(ticker)
                store.cache_set(nyt_key, articles)
            except RuntimeError:
                articles = []  # rate-limited or unavailable — show ticker without articles

        summary_key = _cache_key("summary", {"ticker": ticker, "article_urls": [a["url"] for a in articles]})
        ai = store.cache_get(summary_key, config.CACHE_TTL_SECONDS)
        if ai is None:
            ai = summarize_articles(ticker, articles)
            store.cache_set(summary_key, ai)

        store.append_mention_history(ticker, row["mention_count"])

        result[ticker] = {
            "ticker": ticker,
            "name": row.get("name", ticker),
            "rank": row.get("rank"),
            "mention_count": row.get("mention_count", 0),
            "upvotes": row.get("upvotes", 0),
            "rank_24h_ago": row.get("rank_24h_ago"),
            "mentions_24h_ago": row.get("mentions_24h_ago", 0),
            "articles": articles,
            "ai": ai,
        }

    return result
