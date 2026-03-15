import streamlit as st

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
NEWSAPI_KEY = st.secrets["NEWSAPI_KEY"]
ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]

# ---------------------------------------------------------------------------
# Categories & Keywords
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Geographic query prefixes
# Categories not listed here have no geo restriction (global)
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
# Trusted source domains (used for post-filter flagging on free tier)
# ---------------------------------------------------------------------------
TRUSTED_SOURCES = [
    "reuters.com", "bloomberg.com", "ft.com", "cnbc.com",
    "barrons.com", "theguardian.com", "bbc.com",
    "straitstimes.com", "businesstimes.com.sg",
    "fintech.global", "esgnews.com",
    "timeout.com",
]

# ---------------------------------------------------------------------------
# LLM model
# ---------------------------------------------------------------------------
LLM_MODEL = "claude-haiku-4-5"
