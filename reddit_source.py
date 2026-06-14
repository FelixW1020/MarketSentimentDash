import re
import time
from datetime import datetime, timezone
from typing import Any

import praw

import config

# Tickers that are common English words — skip standalone match to avoid noise
STOP_TICKERS = {"A", "AN", "BE", "FOR", "GO", "IT", "ME", "ON", "OR", "SO", "TO", "UP"}

_reddit: praw.Reddit | None = None


def _get_reddit() -> praw.Reddit:
    global _reddit
    if _reddit is None:
        _reddit = praw.Reddit(
            client_id=config.REDDIT_CLIENT_ID,
            client_secret=config.REDDIT_CLIENT_SECRET,
            user_agent=config.REDDIT_USER_AGENT,
        )
    return _reddit


def _mention_pattern(ticker: str) -> re.Pattern:
    return re.compile(
        rf"(?<![A-Za-z$])(\${re.escape(ticker)}|{re.escape(ticker)})(?![A-Za-z])",
        re.IGNORECASE,
    )


def get_mentions(
    tickers: list[str],
    lookback_hours: int = config.LOOKBACK_HOURS,
    post_limit: int = config.WSB_POST_LIMIT,
) -> dict[str, Any]:
    reddit = _get_reddit()
    subreddit = reddit.subreddit("wallstreetbets")
    cutoff = time.time() - lookback_hours * 3600

    patterns = {
        t: _mention_pattern(t)
        for t in tickers
        if t not in STOP_TICKERS
    }

    seen_ids: set[str] = set()
    posts: list[Any] = []

    try:
        for listing in (subreddit.new(limit=post_limit), subreddit.hot(limit=min(post_limit, 100))):
            for post in listing:
                if post.id in seen_ids:
                    continue
                if post.created_utc < cutoff:
                    continue
                seen_ids.add(post.id)
                posts.append(post)
    except Exception as exc:
        raise RuntimeError(f"Reddit API error: {exc}") from exc

    results: dict[str, Any] = {}
    for ticker in tickers:
        results[ticker] = {
            "mention_count": 0,
            "post_count": 0,
            "top_posts": [],
            "_scored_posts": [],
        }

    for post in posts:
        text = f"{post.title} {post.selftext or ''}"
        for ticker, pattern in patterns.items():
            count = len(pattern.findall(text))
            if count:
                results[ticker]["mention_count"] += count
                results[ticker]["post_count"] += 1
                results[ticker]["_scored_posts"].append(
                    {
                        "title": post.title,
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "permalink": f"https://reddit.com{post.permalink}",
                        "created_utc": datetime.fromtimestamp(
                            post.created_utc, tz=timezone.utc
                        ).isoformat(),
                    }
                )

    for ticker in tickers:
        scored = sorted(
            results[ticker]["_scored_posts"],
            key=lambda p: p["score"],
            reverse=True,
        )[:5]
        results[ticker]["top_posts"] = scored
        del results[ticker]["_scored_posts"]

    return results
