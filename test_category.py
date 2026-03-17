"""
Quick category tester — run a single category fetch without starting Streamlit.

Usage:
    python test_category.py                  # list all categories
    python test_category.py 5                # fetch category #5 by index
    python test_category.py "fintech"        # fetch by partial name (case-insensitive)
    python test_category.py all              # fetch every category (uses API quota!)
"""

import sys
from datetime import datetime, timedelta, timezone

# ── bootstrap: replicate st.secrets so config.py doesn't crash ──────────────
import os
import toml

class _FakeSecrets(dict):
    """Dict that returns '' for missing keys instead of raising KeyError."""
    def __missing__(self, key):
        return ""
    def get(self, key, default=""):
        return super().get(key, default)

secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
_data = toml.load(secrets_path) if os.path.exists(secrets_path) else {}

import streamlit as _st
_st.secrets = _FakeSecrets(_data)
# ─────────────────────────────────────────────────────────────────────────────

from config import CATEGORIES
from news_fetcher import fetch_articles_for_category, _get_window_hours, is_off_hours


CATEGORY_KEYS = list(CATEGORIES.keys())


def list_categories():
    print("\nAvailable categories:")
    for i, name in enumerate(CATEGORY_KEYS):
        print(f"  [{i:2d}] {name}")
    print()


def _resolve_category(arg: str) -> list[str]:
    """Return matching category key(s) for a given argument."""
    if arg.lower() == "all":
        return CATEGORY_KEYS

    # Try index
    try:
        idx = int(arg)
        return [CATEGORY_KEYS[idx]]
    except (ValueError, IndexError):
        pass

    # Try partial name match
    matches = [k for k in CATEGORY_KEYS if arg.lower() in k.lower()]
    if matches:
        return matches

    print(f"  No category matching '{arg}'. Run with no arguments to see the list.")
    sys.exit(1)


def fetch_and_print(category: str, window_start: datetime, window_hours: int):
    print(f"\n{'─'*60}")
    print(f"  {category}")
    print(f"  Window: last {window_hours}h  (from {window_start.strftime('%Y-%m-%d %H:%M')} UTC)")
    print(f"{'─'*60}")

    try:
        articles = fetch_articles_for_category(category, window_start)
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    if not articles:
        print("  No articles found.")
        return

    for i, a in enumerate(articles, 1):
        trusted_flag = "✓ trusted" if a.get("trusted") else "· unverified"
        pub = a.get("published_at", "")[:16].replace("T", " ")
        print(f"\n  [{i}] {a['title']}")
        print(f"       Source : {a['source']}  {trusted_flag}")
        print(f"       Published : {pub}")
        print(f"       URL : {a['url']}")


def main():
    if len(sys.argv) < 2:
        list_categories()
        print("Pass a category number, partial name, or 'all' to fetch.")
        sys.exit(0)

    arg = " ".join(sys.argv[1:])
    categories = _resolve_category(arg)

    window_hours = _get_window_hours()
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    off = is_off_hours()
    print(f"\nMode: {'OFF-HOURS (48h window)' if off else 'WEEKDAY (24h window)'}")

    for cat in categories:
        fetch_and_print(cat, window_start, window_hours)

    print()


if __name__ == "__main__":
    main()
