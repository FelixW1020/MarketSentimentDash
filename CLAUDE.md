# CLAUDE.md — WSB Ticker × NYT News Dashboard

This file is a runbook for **Claude Code**. Drop it at the root of a new project
folder, open Claude Code in that folder, and tell it: *"Read CLAUDE.md and build
the project."* Claude Code should execute the phases below in order, pausing where
noted for API keys.

---

## 1. What we're building

A **local web dashboard** that, for one or more stock tickers:

1. Pulls how often each ticker is mentioned on **r/wallstreetbets** (Reddit API).
2. Pulls recent related coverage from **The New York Times** (NYT Article Search API).
3. Generates **AI summaries** of the NYT coverage and an overall sentiment read
   (Anthropic API).
4. Renders everything in a **browser dashboard** served locally: mention counts,
   a mention-over-time trend, the top WSB posts, and the NYT summary side by side.

**Out of scope (do not build):** options pricing / value projections. Leave a clearly
marked extension point so it can be added later, but build nothing for it now.

**Not financial advice.** The dashboard is informational. Add a visible disclaimer
in the UI footer and the README.

---

## 2. Tech stack (use these unless there's a strong reason not to)

- **Language:** Python 3.11+
- **Reddit:** `praw` (handles OAuth + rate limiting)
- **NYT:** plain `requests` against the Article Search API
- **AI summaries:** `anthropic` SDK (model: `claude-sonnet-4-6`; fall back to
  `claude-haiku-4-5-20251001` for cost)
- **Backend:** `Flask` (single small app; one JSON endpoint + one HTML page)
- **Frontend:** one `index.html` with **Chart.js** from CDN — no build step, no npm
- **Config:** `python-dotenv` reading a `.env` file
- **Cache:** local `sqlite3` (stdlib) so repeated runs don't re-hit APIs

Keep it a **single small repo, no framework beyond Flask.** Favor readability over
cleverness.

---

## 3. Target file layout

```
wsb-nyt-dashboard/
├── CLAUDE.md              # this file
├── README.md             # generated in Phase 6
├── requirements.txt
├── .env.example          # template, committed
├── .env                  # real keys, gitignored — never commit
├── .gitignore
├── config.py             # loads env, defines tickers & tunables
├── reddit_source.py      # WSB mention counts + top posts
├── nyt_source.py         # NYT article fetch
├── summarize.py          # Anthropic summaries + sentiment
├── store.py              # sqlite cache + historical mention snapshots
├── pipeline.py           # orchestrates: reddit + nyt + summary -> dict/db
├── app.py                # Flask: serves dashboard + /api/data
└── templates/
    └── index.html        # dashboard UI (Chart.js)
```

---

## 4. API setup (PAUSE — needs the user)

Before writing integration code, confirm the user has these. Generate `.env.example`
first, then ask the user to fill in `.env`. **Never print secrets back to the chat.**

`.env.example`:

```
# Reddit — https://www.reddit.com/prefs/apps  (create a "script" app)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=wsb-dashboard/0.1 by u/yourname

# NYT — https://developer.nytimes.com  (enable "Article Search API" on an app)
NYT_API_KEY=

# Anthropic — https://console.anthropic.com
ANTHROPIC_API_KEY=

# Optional tunables
TICKERS=GME,TSLA,NVDA
LOOKBACK_HOURS=24
WSB_POST_LIMIT=400
```

Key gotchas to tell the user:
- Reddit app type must be **"script"**; the client ID is the string under the app name.
- NYT Article Search is rate-limited to ~**5 req/sec and 500/day** — the cache matters.
- Reddit free API allows ~**100 queries/min** for OAuth script apps.

---

## 5. Build phases (execute in order)

### Phase 0 — Scaffold
- Create the folder layout and `requirements.txt`:
  `praw requests anthropic flask python-dotenv`.
- Create `.gitignore` (`.env`, `__pycache__/`, `*.db`, `.venv/`).
- Create a venv and install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

### Phase 1 — `config.py`
- Load `.env` via dotenv. Expose: ticker list, lookback window, post limit, model name.
- Validate required keys are present; raise a clear error naming any missing key.

### Phase 2 — `reddit_source.py`
- Init `praw.Reddit` from env.
- `get_mentions(tickers, lookback_hours, post_limit)`:
  - Pull recent `r/wallstreetbets` posts (`new` + `hot`, dedup by id), filtered to the
    lookback window by `created_utc`.
  - Count mentions per ticker in **title + selftext**. Match the bare symbol and the
    `$TICKER` form, case-insensitive, **word-boundaried** to avoid substring noise
    (e.g. don't let "A" or "ON" match everything). Maintain a small stop-set for
    tickers that are common English words.
  - Return per ticker: `mention_count`, `post_count`, and the **top 5 posts** by score
    (title, score, num_comments, permalink, created_utc).
- Be defensive about Reddit rate limits (praw handles most; catch + surface errors).

### Phase 3 — `nyt_source.py`
- `get_articles(query, lookback_days=7, page_limit=2)` against Article Search API.
  - For each ticker, query by company name **and** symbol (maintain a small
    `TICKER -> company name` map; if unknown, fall back to the symbol).
  - Sort by newest. Return per article: headline, abstract, url, pub_date, byline.
  - Respect rate limits: sleep ~250ms between calls.

### Phase 4 — `summarize.py`
- Using the Anthropic SDK, given a ticker + its NYT articles:
  - Produce a **3–4 sentence plain-language summary** of what the news says.
  - Produce a **sentiment label** (Bullish / Neutral / Bearish) **with one line of
    rationale** — clearly framed as "tone of coverage," not a recommendation.
  - Return structured JSON; ask the model to respond in JSON and parse defensively.
- If there are no NYT articles for a ticker, skip the API call and return a "no recent
  coverage" placeholder.

### Phase 5 — `store.py` + `pipeline.py`
- `store.py`: sqlite with two tables — `cache` (key, payload, fetched_at) for raw API
  responses with a TTL (default 30 min), and `mention_history` (ticker, ts,
  mention_count) so the dashboard can plot a **trend over time** across runs.
- `pipeline.py`: `run(tickers)` ->
  1. reddit mentions (cache-aware)
  2. nyt articles (cache-aware)
  3. ai summary per ticker
  4. append mention counts to `mention_history`
  5. return one assembled dict keyed by ticker.

### Phase 6 — `app.py` + `templates/index.html`
- Flask:
  - `GET /` -> render `index.html`.
  - `GET /api/data` -> run the pipeline (or read fresh cache) and return JSON.
  - `GET /api/history` -> return `mention_history` for the trend chart.
- `index.html` (Chart.js via CDN):
  - **Top bar:** ticker selector + refresh button + last-updated time.
  - **Mention card** per ticker: big mention count, post count.
  - **Trend chart:** mentions over time (from `/api/history`).
  - **WSB posts table:** top 5 posts, linked to Reddit.
  - **NYT panel:** AI summary + sentiment badge, then the article list (linked).
  - **Footer disclaimer:** "Informational only. Not financial advice."
  - `<!-- EXTENSION POINT: options projections panel goes here -->` — leave empty.
- Write `README.md`: setup, `.env` instructions, and the run command.

---

## 6. Run it

```bash
source .venv/bin/activate
python app.py            # serves http://127.0.0.1:5000
```

Open the URL in a browser. First load will hit the APIs; subsequent loads within the
cache TTL are instant.

Optional smoke test before wiring the UI:
```bash
python -c "from pipeline import run; import json; print(json.dumps(run(['GME']), indent=2, default=str))"
```

---

## 7. Definition of done

- `python app.py` serves a working dashboard at localhost.
- For each configured ticker the page shows: WSB mention count, a trend chart, top WSB
  posts (linked), an AI NYT summary with a sentiment badge, and linked NYT articles.
- No secrets are committed; `.env` is gitignored and `.env.example` exists.
- Missing/invalid API keys fail with a clear, actionable message.
- A visible "not financial advice" disclaimer is present.
- The options-projection extension point exists but is empty.

## 8. Guardrails for Claude Code

- Pause and ask the user before any step that needs real API keys; never echo secrets.
- Don't add the options/projections feature — it's explicitly deferred.
- Keep dependencies minimal (the five in `requirements.txt`); don't introduce a JS build
  step or a heavier web framework.
- Handle empty results gracefully (a quiet news day or zero WSB mentions must not crash
  the page).
- Cache aggressively to stay under NYT's daily limit while developing.
```
