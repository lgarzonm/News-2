import re
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from newsapi import NewsApiClient

from config import (
    NEWSAPI_KEY,
    GNEWS_API_KEY,
    GUARDIAN_API_KEY,
    CATEGORIES,
    WEEKEND_KEYWORDS,
    GEO_PREFIX,
    TRUSTED_SOURCES,
    BLOCKED_DOMAINS,
    TITLE_REQUIRED_TERMS,
    TITLE_CONTEXT_TERMS,
    TITLE_GLOBAL_BYPASS_TERMS,
    GUARDIAN_SECTIONS,
    RSS_FEEDS,
)

_newsapi_client = NewsApiClient(api_key=NEWSAPI_KEY)

ENTERTAINMENT_CATEGORY = "🎭 Entertainment (Singapore)"
GNEWS_BASE_URL         = "https://gnews.io/api/v4/search"
GUARDIAN_BASE_URL      = "https://content.guardianapis.com/search"


# ---------------------------------------------------------------------------
# Off-hours detection & dynamic window
# ---------------------------------------------------------------------------

def is_off_hours() -> bool:
    """
    Returns True on weekends and Monday pre-market (before 01:00 UTC / 09:00 SGT).
    During off-hours the app uses weekend keywords and a wider time window.
    """
    now = datetime.now(timezone.utc)
    if now.weekday() in (5, 6):          # Saturday = 5, Sunday = 6
        return True
    if now.weekday() == 0 and now.hour < 1:   # Monday pre-market
        return True
    return False


def _get_window_hours() -> int:
    """24 h on weekdays, 72 h on weekends/off-hours to catch Friday + weekend content."""
    return 48 if is_off_hours() else 24


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _is_within_window(published_at_str: str, window_start: datetime) -> bool:
    try:
        dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        return dt >= window_start
    except Exception:
        return False


def _is_trusted(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(domain in t for domain in TRUSTED_SOURCES)


_STOPWORDS = frozenset({
    "the", "and", "for", "from", "with", "that", "this", "have", "will",
    "been", "are", "was", "were", "its", "into", "about", "over", "says",
    "said", "also", "than", "more", "after", "they", "their", "amid",
    "would", "could", "new", "top", "how", "why", "amid", "has", "its",
})


def _sig_words(title: str) -> frozenset:
    """Extract significant tokens from a title for same-story detection.
    Keeps words ≥3 chars OR pure numeric tokens ≥2 chars (funding amounts
    like '36', '500' are strong story identifiers), then removes stopwords."""
    tokens = re.findall(r"[a-z0-9]+", title.lower())
    return frozenset(
        t for t in tokens
        if t not in _STOPWORDS and (len(t) >= 3 or (t.isdigit() and len(t) >= 2))
    )


def _is_same_story(title_a: str, title_b: str, threshold: float = 0.6) -> bool:
    """Return True if two titles cover the same news event.

    Uses word-overlap ratio: shared significant words / min(words in either title).
    A threshold of 0.6 means 60% of the shorter title's key words appear in
    the other — enough to catch rephrased syndicated articles while avoiding
    false positives between genuinely different stories in the same sector.
    """
    a = _sig_words(title_a)
    b = _sig_words(title_b)
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= threshold


def _is_blocked(url: str) -> bool:
    """Return True if the article URL belongs to a blocked domain."""
    if not url:
        return False
    u = url.lower()
    return any(domain in u for domain in BLOCKED_DOMAINS)


def _is_title_relevant(title: str, category: str) -> bool:
    """
    Three-layer title gate:

    1. BYPASS: If the title signals a major global event (war, coup, sanctions,
       missile strike, financial crisis…), pass immediately — these belong in
       the Regional briefing regardless of geography.
    2. GEO/TOPIC GATE: Title must contain at least one term from
       TITLE_REQUIRED_TERMS (geographic or topic anchor).
    3. CONTEXT GATE: If TITLE_CONTEXT_TERMS is defined, title must also
       contain an economic/financial context term (AND with layer 2).

    This lets through: APAC macro news + major world events.
    This blocks: corporate tech deals that happen to mention "Southeast Asia".
    """
    required = TITLE_REQUIRED_TERMS.get(category)
    if not required:
        return True   # no filter defined for this category — allow all
    t = title.lower()
    # Layer 1 — global event bypass
    bypass = TITLE_GLOBAL_BYPASS_TERMS.get(category)
    if bypass and any(term in t for term in bypass):
        return True
    # Layer 2 — geo/topic gate
    if not any(term in t for term in required):
        return False
    # Layer 3 — economic context gate
    context = TITLE_CONTEXT_TERMS.get(category)
    if context and not any(term in t for term in context):
        return False
    return True


def _get_keywords(category: str) -> list[str]:
    """Return weekend or weekday keyword list depending on current time."""
    if is_off_hours():
        return WEEKEND_KEYWORDS.get(category, CATEGORIES[category])
    return CATEGORIES[category]


def _build_keyword_query(category: str) -> str:
    """OR-batch all keywords for a category into one query string."""
    keywords = _get_keywords(category)
    keyword_part = " OR ".join(f'"{kw}"' if " " in kw else kw for kw in keywords)
    geo = GEO_PREFIX.get(category)
    if geo:
        return f"({keyword_part}) AND ({geo})"
    return f"({keyword_part})"


def _normalise_article(raw: dict, category: str) -> dict:
    """Map raw article fields (works for NewsAPI, GNews, Guardian, and RSS shapes)."""
    source_block = raw.get("source", {})
    source_name  = source_block.get("name", "") if isinstance(source_block, dict) else str(source_block)
    source_url   = source_block.get("url", "") if isinstance(source_block, dict) else ""
    url          = raw.get("url", "")
    trusted      = _is_trusted(url) or _is_trusted(source_url) or _is_trusted(source_name)

    return {
        "category":     category,
        "title":        raw.get("title", ""),
        "description":  (raw.get("description") or "")[:200],
        "url":          url,
        "source":       source_name,
        "published_at": raw.get("publishedAt", ""),
        "trusted":      trusted,
    }


def _merge_unique(base: list[dict], new_articles: list[dict], limit: int = 2) -> list[dict]:
    """Append articles from new_articles that aren't already in base, up to limit total.
    Deduplicates by both URL (exact) and title similarity (same-story detection)."""
    seen_urls   = {a["url"] for a in base}
    seen_titles = [a["title"] for a in base]
    result = list(base)
    for a in new_articles:
        if len(result) >= limit:
            break
        if not a["url"] or a["url"] in seen_urls:
            continue
        if any(_is_same_story(a["title"], t) for t in seen_titles):
            continue
        result.append(a)
        seen_urls.add(a["url"])
        seen_titles.append(a["title"])
    return result


# ---------------------------------------------------------------------------
# NewsAPI fetcher
# ---------------------------------------------------------------------------

def _fetch_via_newsapi(category: str, window_start: datetime) -> list[dict]:
    from_param = window_start.strftime("%Y-%m-%dT%H:%M:%S")
    query = _build_keyword_query(category)

    kwargs = {
        "q":          query,
        "from_param": from_param,
        "sort_by":    "publishedAt",
        "page_size":  10,
        "language":   "en",
    }
    # NOTE: do NOT add sources= here — NewsAPI source IDs are unreliable on
    # the free tier. Entertainment quality is controlled by GEO_PREFIX
    # ("Singapore") in the query and by the Time Out Singapore RSS feed.

    try:
        response = _newsapi_client.get_everything(**kwargs)
    except Exception as e:
        raise RuntimeError(str(e)) from e

    if response.get("status") != "ok":
        code = response.get("code", "unknown")
        msg  = response.get("message", "no message")
        raise RuntimeError(f"{code}: {msg}")

    found: list[dict] = []
    seen_urls:   set[str]  = set()
    seen_titles: list[str] = []
    for raw in response.get("articles", []):
        if len(found) >= 2:
            break
        title = raw.get("title", "")
        url   = raw.get("url", "")
        if not title or title == "[Removed]":
            continue
        if not url or url == "https://removed.com":
            continue
        if url in seen_urls:
            continue
        if _is_blocked(url):
            continue
        if not _is_within_window(raw.get("publishedAt", ""), window_start):
            continue
        if not _is_title_relevant(title, category):
            continue
        if any(_is_same_story(title, t) for t in seen_titles):
            continue
        seen_urls.add(url)
        seen_titles.append(title)
        found.append(_normalise_article(raw, category))

    return found


# ---------------------------------------------------------------------------
# GNews fetcher
# ---------------------------------------------------------------------------

def _gnews_single_keyword(keyword: str, geo: str | None, from_param: str) -> list[dict]:
    """One GNews request for a single keyword (GNews rejects long boolean queries)."""
    q = f"{keyword} {geo}" if geo else keyword
    params = {
        "q":      q,
        "from":   from_param,
        "sortby": "publishedAt",
        "max":    5,
        "lang":   "en",
        "token":  GNEWS_API_KEY,
    }
    resp = requests.get(GNEWS_BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GNews error: {data['errors']}")
    return data.get("articles", [])


def _fetch_via_gnews(category: str, window_start: datetime) -> list[dict]:
    if not GNEWS_API_KEY:
        return []

    from_param = window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    geo          = GEO_PREFIX.get(category)
    found:       list[dict] = []
    seen_urls:   set[str]   = set()
    seen_titles: list[str]  = []

    for keyword in _get_keywords(category):
        if len(found) >= 2:
            break
        try:
            articles = _gnews_single_keyword(keyword, geo, from_param)
        except Exception:
            continue   # skip this keyword, try the next

        for raw in articles:
            if len(found) >= 2:
                break
            title = raw.get("title", "")
            url   = raw.get("url", "")
            if not title or not url:
                continue
            if url in seen_urls:
                continue
            if _is_blocked(url):
                continue
            if not _is_within_window(raw.get("publishedAt", ""), window_start):
                continue
            if not _is_title_relevant(title, category):
                continue
            if any(_is_same_story(title, t) for t in seen_titles):
                continue
            seen_urls.add(url)
            seen_titles.append(title)
            found.append(_normalise_article(raw, category))

    return found


# ---------------------------------------------------------------------------
# Guardian API fetcher  (free, 500 req/day, no indexing delay)
# Register at https://open-platform.theguardian.com/
# ---------------------------------------------------------------------------

def _fetch_via_guardian(category: str, window_start: datetime) -> list[dict]:
    if not GUARDIAN_API_KEY:
        return []
    if category not in GUARDIAN_SECTIONS:
        return []

    keywords = _get_keywords(category)
    # Guardian works best with a focused keyword query (first 5 keywords)
    q = " OR ".join(keywords[:5])

    params = {
        "q":           q,
        "section":     GUARDIAN_SECTIONS[category],
        "from-date":   window_start.strftime("%Y-%m-%d"),
        "order-by":    "newest",
        "show-fields": "trailText",
        "page-size":   5,
        "api-key":     GUARDIAN_API_KEY,
    }

    try:
        resp = requests.get(GUARDIAN_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = data.get("response", {}).get("results", [])
    found: list[dict] = []

    for item in results:
        if len(found) >= 2:
            break
        pub_date = item.get("webPublicationDate", "")
        if not _is_within_window(pub_date, window_start):
            continue
        raw = {
            "title":       item.get("webTitle", ""),
            "description": item.get("fields", {}).get("trailText", ""),
            "url":         item.get("webUrl", ""),
            "publishedAt": pub_date,
            "source":      {"name": "The Guardian", "url": "theguardian.com"},
        }
        if not raw["title"] or not raw["url"]:
            continue
        if not _is_title_relevant(raw["title"], category):
            continue
        found.append(_normalise_article(raw, category))

    return found


# ---------------------------------------------------------------------------
# RSS fetcher  (feedparser — free, no API key, real-time)
# Used for categories where API sources have weak coverage.
# ---------------------------------------------------------------------------

def _fetch_via_rss(category: str, window_start: datetime) -> list[dict]:
    feed_urls = RSS_FEEDS.get(category, [])
    if not feed_urls:
        return []

    found:       list[dict] = []
    seen_urls:   set[str]   = set()
    seen_titles: list[str]  = []

    for feed_url in feed_urls:
        if len(found) >= 2:
            break
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in feed.entries:
            if len(found) >= 2:
                break
            url   = entry.get("link", "")
            title = entry.get("title", "")
            if not url or not title or url in seen_urls:
                continue
            if any(_is_same_story(title, t) for t in seen_titles):
                continue

            # Parse publication date from RSS entry
            pub_str = ""
            if hasattr(entry, "published"):
                pub_str = entry.published
            elif hasattr(entry, "updated"):
                pub_str = entry.updated

            # feedparser provides parsed time as a time.struct_time
            pub_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                import calendar
                pub_dt = datetime.fromtimestamp(
                    calendar.timegm(entry.published_parsed), tz=timezone.utc
                )
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                import calendar
                pub_dt = datetime.fromtimestamp(
                    calendar.timegm(entry.updated_parsed), tz=timezone.utc
                )

            if pub_dt is None or pub_dt < window_start:
                continue

            description = ""
            if hasattr(entry, "summary"):
                description = entry.summary[:200]

            # Derive source name from feed URL
            source_name = feed.feed.get("title", feed_url.split("/")[2])

            if _is_blocked(url):
                continue
            if not _is_title_relevant(title, category):
                continue
            raw = {
                "title":       title,
                "description": description,
                "url":         url,
                "publishedAt": pub_dt.isoformat(),
                "source":      {"name": source_name, "url": feed_url.split("/")[2]},
            }
            seen_urls.add(url)
            seen_titles.append(title)
            found.append(_normalise_article(raw, category))

    return found


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

_RATE_LIMIT_MARKERS = (
    "ratelimited", "429", "426", "401",
    "apikeydisabled", "apikeyexhausted", "maximumresultsreached",
)


def _is_rate_limit_error(err_lower: str) -> bool:
    return any(m in err_lower for m in _RATE_LIMIT_MARKERS)


def fetch_articles_for_category(category: str, window_start: datetime) -> list[dict]:
    """
    Full fallback chain — each source is tried in order and results are merged
    until we have 2 articles.  Returns whatever was found (may be 0–2 articles).

    Chain: NewsAPI → GNews → Guardian API → RSS
    Fallback triggers on BOTH rate-limit errors AND fewer-than-2 results, so
    a quiet weekend (0 results from NewsAPI) correctly continues to the next source.
    """
    articles: list[dict] = []

    # 1. NewsAPI
    try:
        articles = _fetch_via_newsapi(category, window_start)
    except RuntimeError as e:
        if not _is_rate_limit_error(str(e).lower()):
            raise  # non-quota errors (bad key, network) bubble up immediately

    if len(articles) >= 2:
        return articles

    # 2. GNews
    try:
        gnews = _fetch_via_gnews(category, window_start)
        articles = _merge_unique(articles, gnews)
    except Exception:
        pass

    if len(articles) >= 2:
        return articles

    # 3. Guardian API
    try:
        guardian = _fetch_via_guardian(category, window_start)
        articles = _merge_unique(articles, guardian)
    except Exception:
        pass

    if len(articles) >= 2:
        return articles

    # 4. RSS (for categories that have feeds configured)
    try:
        rss = _fetch_via_rss(category, window_start)
        articles = _merge_unique(articles, rss)
    except Exception:
        pass

    return articles


def fetch_all_categories() -> dict[str, list[dict]]:
    """
    Fetch articles for all 11 categories.
    Uses a dynamic time window: 24 h on weekdays, 72 h on weekends/off-hours.
    Per-category errors are recorded as {"error": <message>} entries so a
    single failing category never aborts the entire run.
    """
    window_hours = _get_window_hours()
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    results: dict[str, list[dict]] = {}
    errors:  dict[str, str]        = {}

    for category in CATEGORIES:
        try:
            results[category] = fetch_articles_for_category(category, window_start)
        except RuntimeError as e:
            results[category] = []
            errors[category]  = str(e)

    if errors:
        if len(errors) == len(CATEGORIES):
            sample = next(iter(errors.values()))
            raise RuntimeError(f"All categories failed. Sample error: {sample}")
        for category, msg in errors.items():
            results[category] = [{"_error": msg}]

    return results, window_hours
