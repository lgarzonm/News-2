# Helicap News — Technical Brief
**Version:** 1.0  
**Author:** Laura Garzon  
**Date:** March 2026  
**Deployment Target:** Streamlit (via Claude Code)

---

## 1. Project Overview

**Helicap News** is a lightweight, single-page Streamlit dashboard that surfaces 1–2 curated, verified news articles per category from trusted sources, published within the last 24 hours of the user's request. The app is designed for a small internal team (2–5 users) at Helicap, with a clean white/navy blue UI, branded with the Helicap identity.

**Core priorities (in order):**
1. Factual accuracy — only real, verifiable articles with working source links
2. Strict 24-hour time window enforcement
3. Minimal token consumption
4. Clean, professional UI

---

## 2. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Streamlit | Fast deployment, Python-native |
| Search API | **NewsAPI.org** (free tier to start) | Best free option for structured news search with date filtering; upgrade to paid for higher volume |
| LLM (summaries + sentiment) | **Anthropic Claude API** (`claude-haiku-3-5`) | Fastest, cheapest Claude model; ideal for short summarization tasks |
| Language | Python 3.11+ | Standard |
| Secrets management | Streamlit `secrets.toml` / `.env` | API keys never hardcoded |

### Why NewsAPI?
- Free tier: 100 requests/day — sufficient for 1–2 articles × 11 categories = ~22 targeted searches/run
- Native `from` date parameter enforces the 24h window at the API level (not post-hoc filtering)
- Returns `publishedAt`, `url`, `source.name`, `title` — everything needed without fetching full article bodies
- Upgrade path: NewsAPI Pro ($449/mo) or switch to **GNews API** (cheaper) when scaling

### Fallback API (if NewsAPI quota is exhausted)
- **GNews API** (free tier: 100 req/day) as a drop-in secondary source

---

## 3. News Categories & Search Keywords

Each category maps to a keyword group. The search function cycles through keywords until it finds 1–2 articles published within the last 24h. This avoids hard category-name matching and broadens recall.

```python
CATEGORIES = {
    "📈 Stocks": [
        "earnings", "stock rally", "stock drop", "IPO", "dividends",
        "buyback", "volatility", "guidance", "valuation", "profits"
    ],
    "💵 Currencies (Fiat / FX)": [
        "dollar", "euro", "DXY", "currency", "FX", "exchange rate",
        "devaluation", "central bank", "rate hike", "inflation"
    ],
    "📊 Indexes": [
        "S&P 500", "Nasdaq", "Dow", "Nikkei", "Hang Seng", "MSCI",
        "market rally", "market selloff", "futures", "ETF"
    ],
    "🌏 Regional (APAC / ASEAN)": [
        "ASEAN", "Southeast Asia", "APAC", "Singapore economy",
        "Indonesia economy", "China stimulus", "Asia growth",
        "trade", "exports", "regional outlook"
    ],
    "🏦 Country Credit": [
        "sovereign debt", "government bonds", "credit rating",
        "Moody's", "Fitch", "S&P rating", "default risk",
        "debt crisis", "fiscal deficit", "bond yields"
    ],
    "💳 Alternative Lending": [
        "private credit", "alternative lending", "SME loans",
        "non-bank lending", "asset-backed", "loan portfolio",
        "credit fund", "lending platform", "structured finance"
    ],
    "💻 Fintech": [
        "fintech", "digital bank", "e-wallet", "payments", "BNPL",
        "digital lending", "open banking", "blockchain",
        "crypto", "financial inclusion"
    ],
    "🚀 Start-ups": [
        "startup funding", "venture capital", "Series A", "Series B",
        "unicorn", "seed round", "acquisition", "founder", "valuation"
    ],
    "🌱 Sustainable Finance": [
        "green bond", "ESG", "sustainability", "climate finance",
        "carbon", "net zero", "energy transition",
        "impact investing", "renewable energy", "climate policy"
    ],
    "📣 Marketing": [
        "branding", "advertising", "digital marketing", "campaign",
        "consumer", "product launch", "social media",
        "growth strategy", "market share"
    ],
    "🎭 Entertainment (Singapore)": [
        "Singapore events", "concert Singapore", "theatre Singapore",
        "festival Singapore", "Marina Bay", "Sentosa events",
        "art exhibition Singapore", "weekend events SG",
        "restaurant Singapore", "new opening Singapore"
    ],
}
```

### Geographic Weighting Logic
- Categories **Regional, Country Credit, Fintech, Alternative Lending, Start-ups, Sustainable Finance**: prepend `"Asia OR ASEAN OR Southeast Asia"` to the query string
- Categories **Stocks, Currencies, Indexes, Marketing**: no geographic restriction (global)
- Category **Entertainment**: prepend `"Singapore"` and restrict to `sources=straits-times,time-out-singapore,the-business-times`

---

## 4. Trusted Sources

The following source IDs are passed to NewsAPI's `sources` or `domains` parameter where supported:

```python
TRUSTED_SOURCES = [
    # Global Finance & News
    "reuters.com", "bloomberg.com", "ft.com", "cnbc.com",
    "barrons.com", "theguardian.com", "bbc.com",
    # Asia / Singapore
    "straitstimes.com", "businesstimes.com.sg",
    # Specialist
    "fintech.global", "esgnews.com",
    # Singapore Entertainment
    "timeout.com",  # timeout.com/singapore
]
```

> **Note:** NewsAPI free tier does not support domain-level filtering — it returns source metadata in the response. The app will post-filter results to flag whether the source matches the trusted list. On paid tiers, `domains=` parameter can enforce this at query time.

---

## 5. Token Minimization Strategy

This is a core constraint. The following rules apply:

| Rule | Implementation |
|---|---|
| **No full article body fetched** | Only `title`, `description` (≤ 200 chars), `url`, `publishedAt`, `source.name` are used |
| **Haiku model for all LLM calls** | `claude-haiku-3-5` is ~20× cheaper than Sonnet per token |
| **Batch all categories in one LLM call** | All 11 articles (1–2 each) are sent to Claude in a single prompt, not 11 separate calls |
| **Minimal prompt** | System prompt is < 100 tokens; article data is structured, not narrative |
| **No streaming** | Single synchronous call; streaming adds overhead for short outputs |
| **Cache results in `st.session_state`** | Results are stored after each run; re-renders don't re-call APIs |

### Estimated token cost per run
- Input: ~11 articles × ~80 tokens (title + description) = ~880 tokens + ~100 system prompt = **~1,000 tokens input**
- Output: ~11 × 60 tokens (summary + sentiment) = **~660 tokens output**
- **Total per run: ~1,660 tokens** → at Haiku pricing (~$0.80/M input, $4/M output) = **< $0.004 per full run**

---

## 6. Application Architecture

```
helicap_news/
│
├── app.py                  # Main Streamlit app
├── news_fetcher.py         # NewsAPI search logic + 24h filtering
├── llm_processor.py        # Claude Haiku batch summarization + sentiment
├── config.py               # Category definitions, keywords, trusted sources
├── requirements.txt
├── .streamlit/
│   └── secrets.toml        # API keys (NEWSAPI_KEY, ANTHROPIC_API_KEY)
└── assets/
    └── logo.png            # Helicap logo (optional)
```

---

## 7. Core Logic — Step by Step

### Step 1: Trigger
User clicks **"Refresh News"** button in the UI. The timestamp of the click is recorded as `run_time`.

### Step 2: Time Window Calculation
```python
from datetime import datetime, timedelta, timezone
window_start = datetime.now(timezone.utc) - timedelta(hours=24)
# Passed to NewsAPI as: from_param=window_start.isoformat()
```

### Step 3: NewsAPI Search (per category)
For each category, iterate through its keyword list and call NewsAPI:
```
GET /v2/everything
  q = "{keyword} AND ({geo_prefix})"
  from = {window_start ISO8601}
  sortBy = publishedAt
  pageSize = 5          ← fetch 5, keep best 1–2 after filtering
  language = en
```
Stop iterating keywords as soon as 1–2 valid articles are found. This minimizes API calls.

**24h enforcement:** Articles are double-checked against `publishedAt` in Python — NewsAPI's `from` parameter is the primary gate, Python is the safety net.

**Fallback if no results:** Broaden query by trying the next keyword in the list. If all keywords exhausted with 0 results, mark category as `"No recent articles found"` (do not extend window — accuracy is the priority).

### Step 4: Batch LLM Call
Collected articles (all categories) are assembled into a single structured prompt:

```
SYSTEM: You are a financial news assistant. For each article below, provide:
1. A 1–2 sentence neutral summary (max 40 words)
2. Sentiment: Positive | Neutral | Negative
Return JSON only. No preamble.

USER:
[
  {"id": 1, "title": "...", "description": "..."},
  {"id": 2, "title": "...", "description": "..."},
  ...
]
```

Response parsed as JSON, matched back to articles by `id`.

### Step 5: Render UI
Results displayed in Streamlit using a card-style layout per category.

---

## 8. UI Design Specification

### Visual Identity
- **App title:** `Helicap News`
- **Tagline/footer:** `Curated by AI · Designed by Laura Garzon`
- **Color palette:**

| Token | Value | Use |
|---|---|---|
| `--navy` | `#0D1F3C` | Header background, category badges |
| `--blue` | `#1A56DB` | Buttons, links, active states |
| `--light-blue` | `#EBF2FF` | Card backgrounds |
| `--white` | `#FFFFFF` | Page background |
| `--accent-gold` | `#F0A500` | Sentiment: Positive |
| `--accent-red` | `#E63946` | Sentiment: Negative |
| `--accent-grey` | `#6B7280` | Sentiment: Neutral, metadata text |
| `--text` | `#111827` | Body text |

- **Fonts:** `DM Sans` (headings) + `Inter` (body/metadata) via Google Fonts injection

### Layout
```
┌──────────────────────────────────────────────────┐
│  🔵 HELICAP NEWS                [Refresh Button] │  ← Navy header bar
│  Last updated: March 15, 2026 · 14:32 SGT        │
├──────────────────────────────────────────────────┤
│  📈 STOCKS          💵 CURRENCIES    📊 INDEXES   │  ← Category tab row
│  🌏 REGIONAL        🏦 COUNTRY CREDIT  💳 ALT LEND│
│  💻 FINTECH         🚀 START-UPS    🌱 SUST FIN  │
│  📣 MARKETING       🎭 ENTERTAINMENT              │
├──────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────┐  │
│  │ 📰 Article Title Here                      │  │  ← Card
│  │ Reuters · March 15, 2026 · 11:04 AM        │  │
│  │ Summary: One to two sentence AI summary... │  │
│  │ 🟡 Positive          [Read Article →]      │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │ 📰 Second Article...                       │  │
│  └────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────┤
│  Curated by AI · Designed by Laura Garzon · 2026 │  ← Footer
└──────────────────────────────────────────────────┘
```

### Streamlit Custom CSS
Apply via `st.markdown("<style>...</style>", unsafe_allow_html=True)` to achieve the navy/white/blue palette since Streamlit's default theme is limited.

---

## 9. Export Functionality

A **"Download as CSV"** button appears after each run:
```python
st.download_button(
    label="⬇ Download CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"helicap_news_{run_date}.csv",
    mime="text/csv"
)
```

CSV columns: `category`, `title`, `source`, `published_at`, `url`, `summary`, `sentiment`

---

## 10. Environment Variables / Secrets

```toml
# .streamlit/secrets.toml
NEWSAPI_KEY = "your_newsapi_key_here"
ANTHROPIC_API_KEY = "your_anthropic_key_here"
```

In code:
```python
import streamlit as st
NEWSAPI_KEY = st.secrets["NEWSAPI_KEY"]
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
```

---

## 11. Requirements File

```
streamlit>=1.32.0
anthropic>=0.25.0
newsapi-python>=0.2.7
pandas>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## 12. Deployment Instructions (for Claude Code)

1. Run `claude` in the project root directory
2. Ask Claude Code to: *"Build the Helicap News Streamlit app from the technical brief"*
3. Set secrets in `.streamlit/secrets.toml`
4. Run locally: `streamlit run app.py`
5. Deploy to **Streamlit Community Cloud** (free):
   - Push repo to GitHub
   - Connect at share.streamlit.io
   - Add secrets in the Streamlit Cloud dashboard (not in the repo)

---

## 13. Key Constraints & Rules Summary

| Constraint | Implementation |
|---|---|
| 24h time window | Enforced at API query level (`from=`) + Python post-filter |
| Real articles only | NewsAPI returns structured metadata with real URLs — no hallucinated links |
| Trusted sources | Post-filter flag on response; domain-restrict on paid tier |
| Token minimization | Haiku model + batch prompt + no full body fetch + session caching |
| 1–2 articles/category | `pageSize=5` fetched, top 1–2 kept after date + source filter |
| No auto-refresh | Manual button only; no scheduled jobs or `st.rerun()` loops |
| Export | CSV download after each run |
| Branding | "Helicap News" title + "Designed by Laura Garzon" footer |

---

## 14. Known Limitations & Mitigations

| Limitation | Mitigation |
|---|---|
| NewsAPI free tier blocks articles >1 month old (not an issue here) | N/A |
| NewsAPI free tier: no full article text | By design — we only need title + description |
| Bloomberg/FT may be paywalled | Links still provided; user accesses via their own subscriptions |
| NewsAPI may not index all trusted sources | Domain filtering on paid tier; free tier uses post-filter flag |
| Rate limit: 100 req/day free | 11 categories × max 3 keyword attempts = 33 calls max/run → safe for 3 runs/day |

---

*End of Technical Brief — Helicap News v1.0*
