import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example to .env and fill in your API keys."
        )
    return val

# Reddit keys are optional — only needed if switching back from ApeWisdom
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "wsb-dashboard/0.1")

NYT_API_KEY = _require("NYT_API_KEY")

ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")

# If TICKERS is set, use that fixed list. Otherwise the pipeline pulls top N from ApeWisdom live.
_tickers_env = os.getenv("TICKERS", "")
TICKERS = [t.strip().upper() for t in _tickers_env.split(",") if t.strip()] if _tickers_env else []
TOP_N = int(os.getenv("TOP_N", "10"))
APE_FILTER = os.getenv("APE_FILTER", "all-stocks")
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "24"))
WSB_POST_LIMIT = int(os.getenv("WSB_POST_LIMIT", "400"))

MODEL_PRIMARY = "claude-sonnet-4-6"
MODEL_FALLBACK = "claude-haiku-4-5-20251001"
CACHE_TTL_SECONDS = 30 * 60
