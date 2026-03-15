from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from config import CATEGORIES
from news_fetcher import fetch_all_categories
from llm_processor import enrich_articles

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Helicap News",
    page_icon="🔵",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS — navy/white/blue palette + Google Fonts
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #FFFFFF;
    color: #111827;
}

/* Header */
.helicap-header {
    background-color: #0D1F3C;
    padding: 1.2rem 2rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
}
.helicap-header h1 {
    font-family: 'DM Sans', sans-serif;
    color: #FFFFFF;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0;
}
.helicap-header .timestamp {
    color: #A0AEC0;
    font-size: 0.85rem;
    margin-top: 0.2rem;
}

/* Category badge */
.category-badge {
    display: inline-block;
    background-color: #0D1F3C;
    color: #FFFFFF;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 0.75rem;
}

/* Article card */
.article-card {
    background-color: #EBF2FF;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid #1A56DB;
}
.article-title {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: #111827;
    margin-bottom: 0.25rem;
}
.article-meta {
    font-size: 0.78rem;
    color: #6B7280;
    margin-bottom: 0.5rem;
}
.article-summary {
    font-size: 0.88rem;
    color: #374151;
    margin-bottom: 0.6rem;
    line-height: 1.5;
}
.sentiment-positive { color: #F0A500; font-weight: 600; font-size: 0.82rem; }
.sentiment-negative { color: #E63946; font-weight: 600; font-size: 0.82rem; }
.sentiment-neutral  { color: #6B7280; font-weight: 600; font-size: 0.82rem; }

.no-articles {
    color: #6B7280;
    font-size: 0.88rem;
    font-style: italic;
    padding: 0.5rem 0;
}

/* Read link */
.read-link a {
    color: #1A56DB;
    font-size: 0.85rem;
    font-weight: 500;
    text-decoration: none;
}
.read-link a:hover { text-decoration: underline; }

/* Refresh button override */
div[data-testid="stButton"] > button {
    background-color: #1A56DB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    width: 100%;
}
div[data-testid="stButton"] > button:hover {
    background-color: #1446B8;
}

/* Footer */
.helicap-footer {
    text-align: center;
    color: #6B7280;
    font-size: 0.78rem;
    padding: 1.5rem 0 0.5rem;
    border-top: 1px solid #E5E7EB;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_timestamp(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y · %I:%M %p UTC")
    except Exception:
        return iso_str


def _sentiment_html(sentiment: str) -> str:
    s = sentiment.strip().capitalize()
    css = {
        "Positive": "sentiment-positive",
        "Negative": "sentiment-negative",
        "Neutral":  "sentiment-neutral",
    }.get(s, "sentiment-neutral")
    icon = {"Positive": "🟡", "Negative": "🔴", "Neutral": "⚪"}.get(s, "⚪")
    return f'<span class="{css}">{icon} {s}</span>'


def _render_article_card(article: dict) -> None:
    title    = article.get("title", "")
    source   = article.get("source", "")
    pub      = _format_timestamp(article.get("published_at", ""))
    summary  = article.get("summary", "") or "Summary unavailable."
    sentiment = article.get("sentiment", "Neutral")
    url      = article.get("url", "#")

    trusted_badge = " ✓" if article.get("trusted") else ""

    st.markdown(f"""
    <div class="article-card">
        <div class="article-title">📰 {title}</div>
        <div class="article-meta">{source}{trusted_badge} · {pub}</div>
        <div class="article-summary">{summary}</div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            {_sentiment_html(sentiment)}
            <span class="read-link"><a href="{url}" target="_blank">Read Article →</a></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _build_dataframe(results: dict) -> pd.DataFrame:
    rows = []
    for category, articles in results.items():
        for a in articles:
            rows.append({
                "category":     category,
                "title":        a.get("title", ""),
                "source":       a.get("source", ""),
                "published_at": a.get("published_at", ""),
                "url":          a.get("url", ""),
                "summary":      a.get("summary", ""),
                "sentiment":    a.get("sentiment", ""),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
last_updated = st.session_state.get("last_updated", "—")
st.markdown(f"""
<div class="helicap-header">
    <div>
        <h1>🔵 Helicap News</h1>
        <div class="timestamp">Last updated: {last_updated}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Refresh button — sits below header, full width via CSS
if st.button("🔄 Refresh News"):
    with st.spinner("Fetching latest articles and generating summaries…"):
        try:
            raw_results = fetch_all_categories()
        except RuntimeError as e:
            err_msg = str(e).lower()
            if "quota exhausted" in err_msg or "429" in err_msg or "426" in err_msg or "ratelimited" in err_msg:
                st.error(
                    "⚠️ NewsAPI daily quota exhausted (100 req/day on free tier). "
                    "GNews fallback also unavailable. Please try again tomorrow or "
                    "add a GNEWS_API_KEY to your secrets."
                )
            else:
                st.error(f"News fetch failed: {e}")
            st.stop()

        # Flatten to a single list for one batched LLM call
        # (skip placeholder error entries from per-category failures)
        all_articles = []
        for articles in raw_results.values():
            for a in articles:
                if "_error" not in a:
                    all_articles.append(a)

        if all_articles:
            try:
                enrich_articles(all_articles)
            except RuntimeError as e:
                st.warning(
                    f"AI summaries unavailable: {e}. "
                    "Showing articles without summaries."
                )

        # Rebuild results dict with enriched articles (already mutated in-place)
        st.session_state["results"] = raw_results
        st.session_state["last_updated"] = (
            datetime.now(timezone.utc).strftime("%B %d, %Y · %H:%M UTC")
        )
        st.rerun()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
results: dict = st.session_state.get("results", {})

if not results:
    st.info("Click **Refresh News** to load the latest articles.")
else:
    # Render each category
    for category in CATEGORIES:
        articles = results.get(category, [])

        st.markdown(f'<div class="category-badge">{category}</div>', unsafe_allow_html=True)

        if not articles:
            st.markdown('<div class="no-articles">No recent articles found in the last 24 hours.</div>', unsafe_allow_html=True)
        elif len(articles) == 1 and "_error" in articles[0]:
            err_lower = articles[0]["_error"].lower()
            if "quota exhausted" in err_lower or "429" in err_lower or "426" in err_lower or "ratelimited" in err_lower:
                st.markdown('<div class="no-articles">⚠️ API quota exhausted for this category. Try again later.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="no-articles">⚠️ Could not fetch articles: {articles[0]["_error"]}</div>', unsafe_allow_html=True)
        else:
            for article in articles:
                _render_article_card(article)

        st.markdown("<br>", unsafe_allow_html=True)

    # CSV download
    df = _build_dataframe(results)
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    st.download_button(
        label="⬇ Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"helicap_news_{run_date}.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="helicap-footer">
    Curated by AI · Designed by Laura Garzon · 2026
</div>
""", unsafe_allow_html=True)
