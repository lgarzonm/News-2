from datetime import datetime, timedelta, timezone

import requests
from newsapi import NewsApiClient

from config import (
    NEWSAPI_KEY,
    GNEWS_API_KEY,
    CATEGORIES,
    GEO_PREFIX,
    ENTERTAINMENT_SOURCES,
    TRUSTED_SOURCES,
)

_newsapi_client = NewsApiClient(api_key=NEWSAPI_KEY)

ENTERTAINMENT_CATEGORY = "🎭 Entertainment (Singapore)"
GNEWS_BASE_URL = "https://gnews.io/api/v4/search"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _is_within_24h(published_at_str: str, window_start: datetime) -> bool:
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


def _build_keyword_query(category: str) -> str:
    """All keywords for a category OR-batched into one query string."""
    keywords = CATEGORIES[category]
    keyword_part = " OR ".join(keywords)
    geo = GEO_PREFIX.get(category)
    if geo:
        return f"({keyword_part}) AND ({geo})"
    return f"({keyword_part})"


def _normalise_article(raw: dict, category: str) -> dict:
    """Map raw article fields (works for both NewsAPI and GNews shapes) to our schema."""
    # GNews uses 'publishedAt' too; source is {'name', 'url'} in GNews vs {'id','name'} in NewsAPI
    source_block = raw.get("source", {})
    source_name  = source_block.get("name", "")
    source_url   = source_block.get("url", "") or source_block.get("id", "")
    url          = raw.get("url", "")
    trusted      = _is_trusted(url) or _is_trusted(source_url)

    return {
        "category":     category,
        "title":        raw.get("title", ""),
        "description":  (raw.get("description") or "")[:200],
        "url":          url,
        "source":       source_name,
        "published_at": raw.get("publishedAt", ""),
        "trusted":      trusted,
    }


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
    if category == ENTERTAINMENT_CATEGORY:
        kwargs["sources"] = ENTERTAINMENT_SOURCES

    try:
        response = _newsapi_client.get_everything(**kwargs)
    except Exception as e:
        raise RuntimeError(str(e)) from e

    if response.get("status") != "ok":
        code = response.get("code", "unknown")
        msg  = response.get("message", "no message")
        raise RuntimeError(f"{code}: {msg}")

    found = []
    seen_urls: set[str] = set()
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
        if not _is_within_24h(raw.get("publishedAt", ""), window_start):
            continue
        seen_urls.add(url)
        found.append(_normalise_article(raw, category))

    return found


# ---------------------------------------------------------------------------
# GNews fetcher (fallback)
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
        raise RuntimeError("GNEWS_API_KEY not set in secrets")

    from_param = window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    geo = GEO_PREFIX.get(category)
    found = []
    seen_urls: set[str] = set()

    for keyword in CATEGORIES[category]:
        if len(found) >= 2:
            break
        try:
            articles = _gnews_single_keyword(keyword, geo, from_param)
        except Exception as e:
            raise RuntimeError(f"GNews request failed: {e}") from e

        for raw in articles:
            if len(found) >= 2:
                break
            title = raw.get("title", "")
            url   = raw.get("url", "")
            if not title or not url:
                continue
            if url in seen_urls:
                continue
            if not _is_within_24h(raw.get("publishedAt", ""), window_start):
                continue
            seen_urls.add(url)
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
    Try NewsAPI first. If rate-limited or quota-exhausted, fall back to GNews.
    Raises RuntimeError with a clear message on total failure.
    """
    newsapi_err = None
    try:
        return _fetch_via_newsapi(category, window_start)
    except RuntimeError as e:
        newsapi_err = e
        err = str(e).lower()
        if not _is_rate_limit_error(err):
            raise  # Non-rate-limit errors bubble up immediately

    # NewsAPI rate-limited → try GNews
    try:
        return _fetch_via_gnews(category, window_start)
    except RuntimeError as gnews_err:
        raise RuntimeError(
            f"API quota exhausted — NewsAPI: {newsapi_err}; GNews: {gnews_err}"
        ) from gnews_err


def fetch_all_categories() -> dict[str, list[dict]]:
    """
    Fetch articles for all 11 categories — 11 API calls total.
    Per-category errors are recorded as {"error": <message>} entries
    so a single failing category never aborts the entire run.
    """
    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
    results: dict[str, list[dict]] = {}
    errors: dict[str, str] = {}

    for category in CATEGORIES:
        try:
            results[category] = fetch_articles_for_category(category, window_start)
        except RuntimeError as e:
            results[category] = []
            errors[category] = str(e)

    # Propagate any quota-exhausted errors so app.py can surface them clearly
    if errors:
        # Check if all categories failed (full quota exhaustion)
        if len(errors) == len(CATEGORIES):
            sample = next(iter(errors.values()))
            raise RuntimeError(f"All categories failed. Sample error: {sample}")
        # Otherwise store partial errors in results for per-category display
        for category, msg in errors.items():
            results[category] = [{"_error": msg}]

    return results
