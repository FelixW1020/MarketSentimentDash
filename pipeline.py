import hashlib
import json
from typing import Any

import config
import store
from nyt_source import get_articles
from reddit_source import get_mentions
from summarize import summarize_articles


def _cache_key(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"


def run(tickers: list[str] | None = None) -> dict[str, Any]:
    store.init_db()
    if tickers is None:
        tickers = config.TICKERS

    reddit_key = _cache_key("reddit", {"tickers": tickers, "hours": config.LOOKBACK_HOURS})
    reddit_data = store.cache_get(reddit_key, config.CACHE_TTL_SECONDS)
    if reddit_data is None:
        reddit_data = get_mentions(tickers)
        store.cache_set(reddit_key, reddit_data)

    result: dict[str, Any] = {}
    for ticker in tickers:
        nyt_key = _cache_key("nyt", {"ticker": ticker})
        articles = store.cache_get(nyt_key, config.CACHE_TTL_SECONDS)
        if articles is None:
            articles = get_articles(ticker)
            store.cache_set(nyt_key, articles)

        summary_key = _cache_key("summary", {"ticker": ticker, "article_urls": [a["url"] for a in articles]})
        ai = store.cache_get(summary_key, config.CACHE_TTL_SECONDS)
        if ai is None:
            ai = summarize_articles(ticker, articles)
            store.cache_set(summary_key, ai)

        mention_info = reddit_data.get(ticker, {
            "mention_count": 0, "post_count": 0, "top_posts": []
        })

        store.append_mention_history(ticker, mention_info["mention_count"])

        result[ticker] = {
            "ticker": ticker,
            "mention_count": mention_info["mention_count"],
            "post_count": mention_info["post_count"],
            "top_posts": mention_info["top_posts"],
            "articles": articles,
            "ai": ai,
        }

    return result
