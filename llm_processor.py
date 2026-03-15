import json
import re
import anthropic

from config import ANTHROPIC_API_KEY, LLM_MODEL

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "You are a financial news assistant. For each article below, provide:\n"
    "1. A 1-2 sentence neutral summary (max 40 words)\n"
    "2. Sentiment: Positive | Neutral | Negative\n"
    "Return a JSON array only. No preamble. Each element: "
    '{"id": <int>, "summary": "<text>", "sentiment": "<Positive|Neutral|Negative>"}'
)


def enrich_articles(all_articles: list[dict]) -> list[dict]:
    """
    Send all articles in one batched Claude Haiku call.
    Adds 'summary' and 'sentiment' keys to each article dict in-place.
    Returns the enriched list.
    """
    if not all_articles:
        return all_articles

    # Build payload — only title + description sent to LLM (token minimization)
    payload = [
        {"id": i, "title": a["title"], "description": a.get("description", "")}
        for i, a in enumerate(all_articles)
    ]

    response_text = _call_llm(payload)
    enrichments = _parse_response(response_text, len(all_articles))

    for item in enrichments:
        idx = item.get("id")
        if idx is not None and 0 <= idx < len(all_articles):
            all_articles[idx]["summary"] = item.get("summary", "")
            all_articles[idx]["sentiment"] = item.get("sentiment", "Neutral")

    # Fill any missing enrichments with safe defaults
    for article in all_articles:
        article.setdefault("summary", "Summary unavailable.")
        article.setdefault("sentiment", "Neutral")

    return all_articles


def _call_llm(payload: list[dict]) -> str:
    """Make the Claude Haiku API call. Retries once on failure."""
    user_message = json.dumps(payload, ensure_ascii=False)

    for attempt in range(2):
        try:
            message = _client.messages.create(
                model=LLM_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            return message.content[0].text
        except Exception as e:
            if attempt == 1:
                raise RuntimeError(f"Claude API call failed: {e}") from e

    return "[]"


def _parse_response(response_text: str, expected_count: int) -> list[dict]:
    """
    Parse the JSON array from the LLM response.
    Handles three common failure modes:
      1. Markdown code fences (```json ... ```)
      2. Preamble text before the JSON array
      3. Truncated/malformed JSON — falls back to empty list so the app degrades
         gracefully (articles shown without summary/sentiment) rather than crashing.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    # Attempt direct parse first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Fallback: extract the first [...] block in case of preamble text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Complete parse failure — return empty so caller uses safe defaults
    return []
