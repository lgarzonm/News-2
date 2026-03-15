from datetime import datetime, timedelta, timezone
from newsapi import NewsApiClient

from config import (
    NEWSAPI_KEY,
    CATEGORIES,
    GEO_PREFIX,
    ENTERTAINMENT_SOURCES,
    TRUSTED_SOURCES,
)

_client = NewsApiClient(api_key=NEWSAPI_KEY)

ENTERTAINMENT_CATEGORY = "🎭 Entertainment (Singapore)"


def _is_within_24h(published_at_str: str, window_start: datetime) -> bool:
    try:
        dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        return dt >= window_start
    except Exception:
        return False


def _is_trusted(source_url: str) -> bool:
    if not source_url:
        return False
    url_lower = source_url.lower()
    return any(domain in url_lower for domain in TRUSTED_SOURCES)


def _build_query(category: str) -> str:
    """
    Build a single OR-batched query from all keywords for the category.
    e.g. 'earnings OR IPO OR dividends AND (Asia OR ASEAN OR Southeast Asia)'
    This uses exactly 1 API call per category instead of 1 per keyword.
    """
    keywords = CATEGORIES[category]
    keyword_part = " OR ".join(keywords)
    geo = GEO_PREFIX.get(category)
    if geo:
        return f"({keyword_part}) AND ({geo})"
    return f"({keyword_part})"


def fetch_articles_for_category(category: str, window_start: datetime) -> list[dict]:
    """
    One API call per category using all keywords batched with OR.
    Returns up to 2 valid articles within the 24h window.
    """
    from_param = window_start.strftime("%Y-%m-%dT%H:%M:%S")
    query = _build_query(category)

    kwargs = {
        "q": query,
        "from_param": from_param,
        "sort_by": "publishedAt",
        "page_size": 10,   # fetch 10, keep best 1–2 after filtering
        "language": "en",
    }

    if category == ENTERTAINMENT_CATEGORY:
        kwargs["sources"] = ENTERTAINMENT_SOURCES

    try:
        response = _client.get_everything(**kwargs)
    except Exception as e:
        raise RuntimeError(f"NewsAPI request failed for [{category}]: {e}") from e

    if response.get("status") != "ok":
        code = response.get("code", "unknown")
        msg  = response.get("message", "no message")
        raise RuntimeError(f"NewsAPI error for [{category}]: {code} — {msg}")

    found = []
    for article in response.get("articles", []):
        if len(found) >= 2:
            break

        published_at = article.get("publishedAt", "")
        url          = article.get("url", "")
        title        = article.get("title", "")
        description  = article.get("description") or ""

        if not title or title == "[Removed]":
            continue
        if not url or url == "https://removed.com":
            continue
        if not _is_within_24h(published_at, window_start):
            continue

        source_name = article.get("source", {}).get("name", "")
        source_id   = article.get("source", {}).get("id", "")
        trusted     = _is_trusted(url) or _is_trusted(source_id)

        found.append({
            "category":     category,
            "title":        title,
            "description":  description[:200],
            "url":          url,
            "source":       source_name,
            "published_at": published_at,
            "trusted":      trusted,
        })

    return found


def fetch_all_categories() -> dict[str, list[dict]]:
    """
    Fetch articles for all 11 categories — exactly 11 API calls total.
    """
    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
    results = {}

    for category in CATEGORIES:
        articles = fetch_articles_for_category(category, window_start)
        results[category] = articles

    return results
