# WSB × NYT Market Sentiment Dashboard

A local web dashboard that tracks how often stock tickers are mentioned on r/wallstreetbets, fetches recent New York Times coverage, and uses Claude AI to summarize the news and assess sentiment.

> **Not financial advice.** This dashboard is informational only.

## Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=wsb-dashboard/0.1 by u/yourname

NYT_API_KEY=your_nyt_key

ANTHROPIC_API_KEY=your_anthropic_key

TICKERS=GME,TSLA,NVDA
LOOKBACK_HOURS=24
WSB_POST_LIMIT=400
```

**Reddit:** Go to https://www.reddit.com/prefs/apps → create a **"script"** app. The client ID is the short string directly under your app name.

**NYT:** Go to https://developer.nytimes.com → create an app → enable **"Article Search API"**.

**Anthropic:** Get a key at https://console.anthropic.com.

### 3. Run

```bash
source .venv/bin/activate
python app.py
```

Open http://127.0.0.1:5000 in your browser.

The first load hits the APIs; subsequent loads within 30 minutes use the local SQLite cache (`dashboard.db`).

## Optional smoke test

```bash
python -c "from pipeline import run; import json; print(json.dumps(run(['GME']), indent=2, default=str))"
```

## Extension point

The options/projections panel is intentionally left empty. Look for this comment in `templates/index.html`:

```html
<!-- EXTENSION POINT: options projections panel goes here -->
```
