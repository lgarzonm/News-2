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
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD",        # major pairs — appear verbatim in FX titles
        "USD/SGD", "USD/MYR", "USD/IDR", "USD/THB",        # APAC pairs
        "dollar index", "DXY", "dollar strengthens", "dollar weakens",
        "greenback", "exchange rate", "forex market",
        "ringgit", "rupiah", "baht", "peso falls", "won strengthens",
        "currency intervention", "FX reserves", "spot rate",
        "central bank rate", "rate hike", "rate cut",
        "currency devaluation", "capital flows",
    ],
    "📊 Indexes": [
        # Use composite/performance phrases — NOT bare "Nasdaq" which matches any NASDAQ-listed company
        "S&P 500", "Dow Jones", "Dow futures", "Dow rises", "Dow falls",
        "Nasdaq Composite", "Nasdaq 100", "Nasdaq futures", "Nasdaq rises", "Nasdaq falls",
        "Nikkei 225", "Hang Seng Index", "MSCI index",
        "market futures", "index futures", "stock index",
        "market rally", "market selloff", "stocks rise", "stocks fall",
        "market closes", "market opens", "weekly close",
    ],
    "🌏 Regional (APAC / ASEAN)": [
        "ASEAN", "Southeast Asia", "APAC", "Asia markets",
        "Singapore economy", "Indonesia economy", "China economy",
        "China stimulus", "Japan economy", "Asia growth",
        "emerging markets", "trade", "exports",
    ],
    "🏦 Country Credit": [
        # Rating agencies — bare names catch any headline with Moody's/Fitch/S&P action
        "Moody's", "Fitch", "S&P", "DBRS", "Scope Ratings",
        # Sovereign / government debt
        "sovereign debt", "sovereign rating", "sovereign credit",
        "government bond", "government debt", "national debt",
        "bond yield", "bond yields", "yield curve",
        # Fiscal / credit events
        "credit rating", "rating downgrade", "rating upgrade",
        "rating cut", "outlook cut", "outlook stable", "outlook negative",
        "fiscal deficit", "fiscal framework", "fiscal policy",
        "debt crisis", "debt default", "default risk",
        # Broader fiscal signals (catches "Thai fiscal framework", "budget review")
        "fiscal", "government budget", "public debt",
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
        "USD/SGD", "USD/MYR", "USD/IDR",
        "forex analysis", "currency forecast", "dollar outlook",
        "FX week ahead", "forex technical analysis",
        "ringgit outlook", "rupiah forecast", "baht outlook",
        "currency market outlook", "FX market preview",
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
    "💻 Fintech":                 "Asia OR ASEAN OR Southeast Asia",
    # Country Credit, Alternative Lending, and Sustainable Finance are global —
    # restricting to Asia misses S&P/Fitch/Moody's global actions, Middle East
    # war credit risk, oil price fiscal stress, etc.
    "🚀 Start-ups":               "Asia OR ASEAN OR Southeast Asia",
    "🎭 Entertainment (Singapore)": "Singapore",
}

# NewsAPI source restriction for Entertainment only
ENTERTAINMENT_SOURCES = "straits-times,time-out-singapore,the-business-times"

# ---------------------------------------------------------------------------
# Trusted source domains  (post-filter flag; domain-restrict on paid tier)
# Weekend-active sources like investing.com and fxstreet.com are included.
# ---------------------------------------------------------------------------
TRUSTED_SOURCES = [
    # ── Tier-1 Global News Wires & Press ───────────────────────────────────
    "reuters.com", "apnews.com", "bloomberg.com", "ft.com",
    "wsj.com", "nytimes.com", "theguardian.com", "bbc.com",
    "economist.com", "cnbc.com", "marketwatch.com",

    # ── Business / Investment Press ────────────────────────────────────────
    "barrons.com", "forbes.com", "fortune.com",
    "businessinsider.com", "morningstar.com",
    "seekingalpha.com", "thestreet.com",

    # ── FX / Forex (24/7 coverage) ────────────────────────────────────────
    "investing.com", "fxstreet.com", "forexlive.com",
    "dailyfx.com", "fxempire.com",

    # ── Asia — Regional Tier-1 ────────────────────────────────────────────
    "nikkei.com", "asia.nikkei.com",          # Nikkei Asia (Japan + APAC)
    "scmp.com",                                # South China Morning Post
    "straitstimes.com",                        # Singapore flagship
    "businesstimes.com.sg",                    # Singapore business
    "channelnewsasia.com",                     # CNA (Singapore/ASEAN)
    "todayonline.com",                         # Singapore Today
    "theedgesingapore.com", "theedgemarkets.com",  # The Edge (SG + MY)
    "thestar.com.my",                          # Malaysia
    "bangkokpost.com",                         # Thailand
    "thejakartapost.com",                      # Indonesia
    "vietnamnews.vn",                          # Vietnam

    # ── APAC Deals / Start-ups / Tech ────────────────────────────────────
    "dealstreetasia.com",  # APAC M&A, VC, PE deals
    "techinasia.com",      # Southeast Asia tech & startups
    "e27.co",              # Singapore/SEA startup ecosystem
    "krasia.com",          # KrASIA — APAC digital economy

    # ── Fintech ────────────────────────────────────────────────────────────
    "fintechnews.sg",      # Singapore fintech
    "fintech.global",      # Global fintech
    "pymnts.com",          # Payments & fintech (US/global)
    "fintechfutures.com",  # Banking & fintech
    "crowdfundinsider.com",# Alt-finance, BNPL, lending platforms

    # ── Alternative Lending / Private Credit ─────────────────────────────
    "altfi.com",
    "privateequitywire.co.uk",
    "privatedebtinvestor.com",

    # ── Sustainable Finance / ESG ─────────────────────────────────────────
    "esgnews.com", "responsible-investor.com",
    "greenbiz.com", "environmentalfinance.com",
    "renewablesnow.com", "climateaction.org",

    # ── Global Tech & Start-ups ───────────────────────────────────────────
    "techcrunch.com", "venturebeat.com",

    # ── Marketing & Advertising ───────────────────────────────────────────
    "adage.com", "marketingweek.com",
    "campaignasia.com",    # Campaign Asia — highly relevant for the region

    # ── Singapore Entertainment & Lifestyle ───────────────────────────────
    "timeout.com",         # Time Out Singapore
    "visitsingapore.com",  # Singapore Tourism Board
    "asiaone.com",         # Singapore lifestyle/events
]

# ---------------------------------------------------------------------------
# Blocked domains — sources known to return off-topic or low-quality results.
# Articles from these domains are discarded regardless of keyword match.
# ---------------------------------------------------------------------------
BLOCKED_DOMAINS = [
    "barchart.com",         # commodity charts — keeps matching FX keywords with cocoa/grain stories
    "triblive.com",         # local Pittsburgh news — zero relevance to finance
    "msn.com",              # aggregator with poor relevance on free-tier keyword queries
    "patch.com",            # hyper-local US community news
    "legacy.com",           # obituaries
    "cryptobreaking.com",   # crypto press releases — matches "Nasdaq listing" SPAC deals
    "marketscreener.com",   # corporate news aggregator — publishes deals/deployments not macro news
    "globenewswire.com",    # raw press releases — company announcements, not market news
    "prnewswire.com",       # same — press releases not editorial news
    "businesswire.com",     # same
]

# ---------------------------------------------------------------------------
# Title relevance terms — post-fetch gate.
# After NewsAPI/GNews return results, we check that the article TITLE contains
# at least one term from this list.  This stops body-matched irrelevant results
# (e.g. a school renovation article that mentions "bond rate" in paragraph 8).
# Terms are matched case-insensitively as substrings of the title.
# ---------------------------------------------------------------------------
TITLE_REQUIRED_TERMS = {
    "📈 Stocks": [
        "stock", "share", "equity", "equities", "market", "earnings",
        "ipo", "dividend", "wall street", "nasdaq", "s&p", "dow",
        "rally", "selloff", "sell-off", "profit", "revenue", "buyback",
    ],
    "💵 Currencies (Fiat / FX)": [
        "dollar", "euro", "yen", "pound", "sterling", "franc", "currency", "currencies",
        "forex", " fx ", "eur/", "usd/", "gbp/", "jpy/", "aud/", "sgd/", "myr/",
        "idr/", "thb/", "ringgit", "rupiah", "baht", "peso", "won", "ruble",
        "exchange rate", "dxy", "greenback", "rate hike", "rate cut",
        "devaluation", "appreciation", "depreciation", "central bank",
    ],
    "📊 Indexes": [
        # Require index-performance language — reject "Nasdaq listing" / "NASDAQ: TICK" articles
        "s&p 500", "dow jones", "dow futures", "dow rises", "dow falls", "dow bounces",
        "nasdaq composite", "nasdaq 100", "nasdaq futures", "nasdaq rises", "nasdaq falls",
        "nikkei 225", "hang seng index", "msci index",
        "market futures", "index futures", "stock index", "stock indices",
        "market rally", "market selloff", "stocks rise", "stocks fall",
        "market closes", "market opens",
    ],
    "🌏 Regional (APAC / ASEAN)": [
        "asia", "asean", "apac", "singapore", "indonesia", "malaysia",
        "thailand", "vietnam", "philippines", "china", "japan", "korea",
        "emerging market", "southeast asia",
    ],
    "🏦 Country Credit": [
        # Rating agency names — any form ("Fitch cuts", "S&P warns", "Moody's downgrades")
        "moody", "fitch", "s&p", "dbrs",
        # Sovereign / debt language
        "bond", "yield", "debt", "sovereign", "default", "fiscal",
        "deficit", "treasury", "government bond", "public debt",
        # Rating action language
        "rating", "downgrade", "upgrade", "credit outlook", "credit risk",
        "credit stability", "credit quality",
    ],
    "💳 Alternative Lending": [
        "lending", "loan", "credit", "financi", "private debt", "private credit",
        "sme", "non-bank", "asset-backed", "structured finance",
    ],
    "💻 Fintech": [
        "fintech", "bank", "payment", "crypto", "blockchain", "digital",
        "wallet", "bnpl", "neobank", "defi", "financial technology",
    ],
    "🚀 Start-ups": [
        "startup", "start-up", "funding", "venture", "series a", "series b",
        "seed", "unicorn", "founder", "vc ", "valuation", "raise",
    ],
    "🌱 Sustainable Finance": [
        "esg", "green bond", "sustainable", "climate", "carbon", "net zero",
        "renewable", "energy transition", "impact invest", "clean energy",
    ],
    "📣 Marketing": [
        "marketing", "advertising", "brand", "campaign", "consumer",
        "ad spend", "social media", "digital marketing", "market share",
    ],
    "🎭 Entertainment (Singapore)": [
        "singapore", "sentosa", "marina bay", "concert", "festival",
        "theatre", "theater", "exhibition", "restaurant", "event",
    ],
}

# ---------------------------------------------------------------------------
# Compound title filter — for categories where a geographic OR topic term
# alone is too broad, the title must ALSO contain at least one of these
# economic/financial context terms.  Implemented as an AND over both lists:
#   _title_matches = geo_term_present AND context_term_present
# ---------------------------------------------------------------------------
TITLE_CONTEXT_TERMS = {
    # "Southeast Asia" / "Asia" appear in countless corporate press releases,
    # tech deployment deals, and infrastructure announcements.  Require that
    # the title also signals economic/financial relevance.
    "🌏 Regional (APAC / ASEAN)": [
        "economy", "economic", "gdp", "growth", "trade", "export", "import",
        "market", "markets", "price", "prices", "inflation", "investment",
        "policy", "rate", "rates", "fund", "finance", "financial",
        "bank", "credit", "debt", "fiscal", "monetary", "forecast",
        "outlook", "oil", "energy", "commodity", "currency", "spending",
        "jobs", "employment", "recession", "stimulus", "budget", "reform",
    ],
}

# ---------------------------------------------------------------------------
# Global event bypass — for the Regional category, major worldwide geopolitical
# or macroeconomic crises bypass the APAC geo + context compound gate entirely.
# These terms signal events so significant they belong in any regional briefing
# regardless of geography (e.g. Iran war, Venezuela coup, global sanctions).
# ---------------------------------------------------------------------------
TITLE_GLOBAL_BYPASS_TERMS = {
    "🌏 Regional (APAC / ASEAN)": [
        # Armed conflict / geopolitical crisis
        "war", "invasion", "coup", "takeover", "overthrow", "uprising", "civil war",
        "airstrike", "air strike", "missile", "nuclear", "troops", "military strike",
        "bombing", "ceasefire", "cease-fire", "sanctions", "conflict", "assassination",
        "siege", "blockade", "offensive", "attack on", "crisis",
        # Major economic shocks
        "global recession", "market crash", "financial crisis", "debt default",
        "oil embargo", "energy crisis", "supply shock",
    ],
}

  — section IDs per category for tighter relevance
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
        "https://feeds.reuters.com/reuters/businessNews",  # covers Deutsche Bank / private credit stories
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
    # Regional & Country Credit: CNA covers ASEAN daily
    "🌏 Regional (APAC / ASEAN)": [
        "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",  # Asia
    ],
    "🏦 Country Credit": [
        "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
        "https://feeds.reuters.com/reuters/businessNews",
    ],
    # Fintech: Fintech News Singapore
    "💻 Fintech": [
        "https://fintechnews.sg/feed/",
    ],
    # Start-ups: Tech in Asia
    "🚀 Start-ups": [
        "https://www.techinasia.com/feed",
    ],
    # Sustainable Finance: Renewables Now + Reuters environment
    "🌱 Sustainable Finance": [
        "https://renewablesnow.com/feed/",
        "https://feeds.reuters.com/reuters/environment",
    ],
}

# ---------------------------------------------------------------------------
# LLM model
# ---------------------------------------------------------------------------
LLM_MODEL = "claude-haiku-4-5"
