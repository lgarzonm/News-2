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
    """Return True if the article's publishedAt is within the 24h window."""
    try:
        dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        return dt >= window_start
    except Exception:
        return False


def _is_trusted(source_url: str) -> bool:
    """Return True if any trusted domain appears in the source URL."""
    if not source_url:
        return False
    url_lower = source_url.lower()
    return any(domain in url_lower for domain in TRUSTED_SOURCES)


def _build_query(keyword: str, category: str) -> str:
    geo = GEO_PREFIX.get(category)
    if geo:
        return f'{keyword} AND ({geo})'
    return keyword


def fetch_articles_for_category(category: str, window_start: datetime) -> list[dict]:
    """
    Iterate through keywords for the category until 1–2 valid articles are found.
    Returns a list of article dicts (max 2).
    """
    keywords = CATEGORIES[category]
    # NewsAPI expects UTC in Z-suffix format, not +00:00
    from_param = window_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    found = []

    for keyword in keywords:
        if len(found) >= 2:
            break

        query = _build_query(keyword, category)
        kwargs = {
            "q": query,
            "from_param": from_param,
            "sort_by": "publishedAt",
            "page_size": 5,
            "language": "en",
        }

        # Entertainment: restrict to specific sources
        if category == ENTERTAINMENT_CATEGORY:
            kwargs["sources"] = ENTERTAINMENT_SOURCES

        try:
            response = _client.get_everything(**kwargs)
        except Exception as e:
            raise RuntimeError(f"NewsAPI request failed for [{category}] keyword '{keyword}': {e}") from e

        if response.get("status") != "ok":
            code = response.get("code", "unknown")
            msg  = response.get("message", "no message")
            raise RuntimeError(f"NewsAPI error for [{category}]: {code} — {msg}")

        for article in response.get("articles", []):
            if len(found) >= 2:
                break

            published_at = article.get("publishedAt", "")
            url = article.get("url", "")
            title = article.get("title", "")
            description = article.get("description") or ""

            # Skip removed / deleted articles
            if not title or title == "[Removed]":
                continue
            if not url or url == "https://removed.com":
                continue

            # Double-check the 24h window in Python
            if not _is_within_24h(published_at, window_start):
                continue

            source_name = article.get("source", {}).get("name", "")
            source_id = article.get("source", {}).get("id", "")
            trusted = _is_trusted(url) or _is_trusted(source_id)

            found.append({
                "category": category,
                "title": title,
                "description": description[:200],
                "url": url,
                "source": source_name,
                "published_at": published_at,
                "trusted": trusted,
            })

    return found


def fetch_all_categories() -> dict[str, list[dict]]:
    """
    Fetch articles for all 11 categories.
    Returns a dict keyed by category name, value is list of article dicts (0–2 each).
    """
    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
    results = {}

    for category in CATEGORIES:
        articles = fetch_articles_for_category(category, window_start)
        results[category] = articles

    return results
