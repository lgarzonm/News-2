import streamlit as st

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
NEWSAPI_KEY      = st.secrets["NEWSAPI_KEY"]
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
GNEWS_API_KEY    = st.secrets.get("GNEWS_API_KEY", "")
GUARDIAN_API_KEY = st.secrets.get("GUARDIAN_API_KEY", "")

# ---------------------------------------------------------------------------
# Categories & Keywords  (weekday — event-driven, phrase-level matching)
# These phrases are chosen to appear verbatim in real article titles/descriptions
# so that NewsAPI's exact-match search actually finds them.
# ---------------------------------------------------------------------------
CATEGORIES = {
    "📈 Stocks": [
        "stock market", "equity markets", "share price", "earnings",
        "stock rally", "stock drop", "Wall Street", "IPO",
        "dividends", "buyback", "quarterly results", "profits",
        "market cap", "valuation", "guidance",
    ],
    "💵 Currencies (Fiat / FX)": [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",        # pair names appear verbatim in FX titles
        "dollar", "DXY", "exchange rate", "central bank",
        "rate hike", "inflation", "currency", "forex",
        "devaluation", "rate cut",
    ],
    "📊 Indexes": [
        "S&P 500", "Nasdaq", "Dow Jones", "Nikkei", "Hang Seng", "MSCI",
        "market rally", "market selloff", "index futures",
        "market futures", "ETF", "weekly close",
    ],
    "🌏 Regional (APAC / ASEAN)": [
        "ASEAN", "Southeast Asia", "APAC", "Asia markets",
        "Singapore economy", "Indonesia economy", "China economy",
        "China stimulus", "Japan economy", "Asia growth",
        "emerging markets", "trade", "exports",
    ],
    "🏦 Country Credit": [
        "sovereign debt", "government bonds", "bond yields",
        "credit rating", "rating upgrade", "rating downgrade",
        "Moody's", "Fitch", "S&P rating", "default risk",
        "yield curve", "fiscal deficit", "debt crisis",
    ],
    "💳 Alternative Lending": [
        "private credit", "private debt", "direct lending",
        "alternative lending", "SME loans", "non-bank lending",
        "asset-backed", "credit fund", "lending platform",
        "structured finance", "loan portfolio",
    ],
    "💻 Fintech": [
        "fintech", "neobank", "digital bank", "digital payments",
        "e-wallet", "payments", "BNPL", "digital lending",
        "open banking", "blockchain", "crypto", "financial inclusion",
    ],
    "🚀 Start-ups": [
        "startup funding", "venture capital", "Series A", "Series B",
        "tech startup", "unicorn", "seed round", "seed funding",
        "acquisition", "pre-IPO", "founder", "valuation",
    ],
    "🌱 Sustainable Finance": [
        "green bond", "ESG", "sustainable finance", "climate finance",
        "carbon credits", "net zero", "energy transition",
        "impact investing", "renewable energy", "climate policy",
        "sustainability",
    ],
    "📣 Marketing": [
        "advertising", "digital marketing", "ad spend",
        "marketing campaign", "consumer trends", "product launch",
        "social media marketing", "growth strategy", "market share",
        "brand strategy",
    ],
    "🎭 Entertainment (Singapore)": [
        "Singapore events", "concert Singapore", "theatre Singapore",
        "festival Singapore", "Marina Bay", "Sentosa events",
        "art exhibition Singapore", "weekend events SG",
        "restaurant Singapore", "new opening Singapore",
    ],
}

# ---------------------------------------------------------------------------
# Weekend / off-hours keywords
# Used on Saturdays, Sundays, and Monday pre-market (before 01:00 UTC).
# These target the *type* of content actually published on off-hours:
# analyst notes, previews, technical analysis, weekly roundups.
# ---------------------------------------------------------------------------
WEEKEND_KEYWORDS = {
    "📈 Stocks": [
        "week ahead markets", "market preview", "stock market outlook",
        "analyst note", "price target", "equity outlook",
        "BofA", "Goldman Sachs", "Morgan Stanley",
        "technical analysis stocks", "market wrap", "weekly performance",
    ],
    "💵 Currencies (Fiat / FX)": [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",
        "forex analysis", "currency forecast", "dollar outlook",
        "FX week ahead", "support level", "resistance level",
        "currency technical analysis",
    ],
    "📊 Indexes": [
        "market outlook week", "index forecast", "S&P 500 outlook",
        "Nasdaq outlook", "market preview week", "technical levels",
        "market analysis", "week ahead equities", "futures outlook",
    ],
    "🌏 Regional (APAC / ASEAN)": [
        "Asia week ahead", "ASEAN outlook", "Asia Pacific markets",
        "emerging markets outlook", "China market outlook",
        "Asia economic outlook", "Southeast Asia economy",
    ],
    "🏦 Country Credit": [
        "bond market outlook", "yield forecast", "credit outlook",
        "sovereign rating", "government debt outlook",
        "bond yields week", "rating action", "fiscal outlook",
    ],
    "💳 Alternative Lending": [
        "private credit outlook", "direct lending market",
        "alternative finance", "credit market update",
        "private debt outlook", "lending market news",
    ],
    "💻 Fintech": [
        "fintech news", "crypto market", "DeFi",
        "digital finance", "payment platform", "neobank",
        "crypto outlook", "blockchain technology",
    ],
    "🚀 Start-ups": [
        "startup news", "venture capital outlook", "VC funding",
        "tech startup funding", "investment round",
        "entrepreneurship", "startup ecosystem",
    ],
    "🌱 Sustainable Finance": [
        "ESG investing", "green finance", "climate change finance",
        "sustainable investment", "clean energy investment",
        "carbon market", "ESG outlook",
    ],
    "📣 Marketing": [
        "marketing news", "advertising industry", "marketing trends",
        "consumer behaviour", "brand news", "digital advertising",
    ],
    "🎭 Entertainment (Singapore)": [
        # Same keywords — weekend content is the norm for this category
        "Singapore events", "concert Singapore", "theatre Singapore",
        "festival Singapore", "Marina Bay", "Sentosa events",
        "art exhibition Singapore", "weekend events SG",
        "restaurant Singapore", "new opening Singapore",
    ],
}

# ---------------------------------------------------------------------------
# Geographic query prefixes
# ---------------------------------------------------------------------------
GEO_PREFIX = {
    "🌏 Regional (APAC / ASEAN)": "Asia OR ASEAN OR Southeast Asia",
    "🏦 Country Credit":          "Asia OR ASEAN OR Southeast Asia",
    "💻 Fintech":                 "Asia OR ASEAN OR Southeast Asia",
    "💳 Alternative Lending":     "Asia OR ASEAN OR Southeast Asia",
    "🚀 Start-ups":               "Asia OR ASEAN OR Southeast Asia",
    "🌱 Sustainable Finance":     "Asia OR ASEAN OR Southeast Asia",
    "🎭 Entertainment (Singapore)": "Singapore",
}

# NewsAPI source restriction for Entertainment only
ENTERTAINMENT_SOURCES = "straits-times,time-out-singapore,the-business-times"

# ---------------------------------------------------------------------------
# Trusted source domains  (post-filter flag; domain-restrict on paid tier)
# Weekend-active sources like investing.com and fxstreet.com are included.
# ---------------------------------------------------------------------------
TRUSTED_SOURCES = [
    # Global Finance & News
    "reuters.com", "bloomberg.com", "ft.com", "cnbc.com",
    "barrons.com", "theguardian.com", "bbc.com",
    "marketwatch.com", "wsj.com",
    # FX / Markets (publish 24/7)
    "investing.com", "fxstreet.com",
    # Analysis / Aggregators
    "seekingalpha.com", "thestreet.com",
    # Asia / Singapore
    "straitstimes.com", "businesstimes.com.sg",
    # Specialist
    "fintech.global", "esgnews.com", "altfi.com",
    # Singapore Entertainment
    "timeout.com",
]

# ---------------------------------------------------------------------------
# Guardian API  — section IDs per category for tighter relevance
# https://open-platform.theguardian.com/  (free, 500 req/day)
# ---------------------------------------------------------------------------
GUARDIAN_SECTIONS = {
    "📈 Stocks":                    "business/stock-markets",
    "💵 Currencies (Fiat / FX)":   "business/currencies",
    "📊 Indexes":                   "business/stock-markets",
    "🌏 Regional (APAC / ASEAN)":  "world/asia-pacific",
    "🏦 Country Credit":            "business/bond-markets",
    "💳 Alternative Lending":       "business",
    "💻 Fintech":                   "technology",
    "🚀 Start-ups":                 "technology",
    "🌱 Sustainable Finance":       "environment",
    "📣 Marketing":                 "media/advertising",
    # Entertainment (SG) intentionally omitted — Guardian has no SG local content
}

# ---------------------------------------------------------------------------
# RSS feeds  — free, no API key, real-time; used as last-resort fallback
# for categories where NewsAPI/GNews/Guardian have weakest coverage.
# feedparser handles the parsing.
# ---------------------------------------------------------------------------
RSS_FEEDS = {
    "💵 Currencies (Fiat / FX)": [
        "https://www.fxstreet.com/rss/news",
        "https://feeds.reuters.com/reuters/USDollarRSS",
    ],
    "💳 Alternative Lending": [
        "https://www.altfi.com/feed",
    ],
    "🎭 Entertainment (Singapore)": [
        "https://www.straitstimes.com/news/life/rss.xml",
    ],
    # Stocks/Indexes: investing.com RSS as extra source
    "📈 Stocks": [
        "https://www.investing.com/rss/news_25.rss",   # equities feed
    ],
    "📊 Indexes": [
        "https://www.investing.com/rss/news_25.rss",
    ],
}

# ---------------------------------------------------------------------------
# LLM model
# ---------------------------------------------------------------------------
LLM_MODEL = "claude-haiku-4-5"
