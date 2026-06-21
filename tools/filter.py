import json
import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM = """You are a research analyst filtering web search results for a specific company.

Rules:
- Only include information that is CLEARLY and SPECIFICALLY about the named target company.
- Discard results about: unrelated companies mentioned in passing, generic industry articles with no company-specific content, page navigation, social share buttons ("Share on Facebook/X/LinkedIn"), cookie notices, newsletter signup text, author bylines unrelated to the company, or any boilerplate not about the company.
- For each category, write a clean 2-4 sentence factual summary using ONLY verified-relevant content.
- If NONE of the results in a category contain information specifically about the target company, return the string "No relevant data found."

Respond ONLY with a valid JSON object — no markdown fences, no explanation."""


def _format_results(results: list[dict]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        content = r.get("content", "").strip()
        lines.append(
            f"  {i}. [{r.get('title', '')}] {r.get('url', '')}\n"
            f"     {content[:500]}"
        )
    return "\n".join(lines) if lines else "  (no results)"


async def filter_research(
    company_name: str,
    domain: str | None,
    raw_data: dict,
) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    company_ref = f"{company_name} ({domain})" if domain else company_name

    categories = ["overview", "news", "tech_stack", "leadership_funding", "ai_devtools", "ai_vision", "hiring_intent", "competitor_tooling", "engineering_pain"]
    blocks = "\n\n".join(
        f"CATEGORY: {key}\n{_format_results(raw_data.get(key, {}).get('results', []))}"
        for key in categories
    )

    user_msg = f"""Filter and summarise these search results for: {company_ref}

Only include content that is specifically and clearly about this company.

{blocks}

Respond with this JSON (use "No relevant data found." if a category has nothing relevant):
{{
  "overview": "...",
  "news": "...",
  "tech_stack": "...",
  "leadership_funding": "...",
  "ai_devtools": "...",
  "ai_vision": "...",
  "hiring_intent": "...",
  "competitor_tooling": "...",
  "engineering_pain": "..."
}}"""

    try:
        response = await client.messages.create(
            model=_MODEL,
            max_tokens=2048,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        text_block = next((b for b in response.content if b.type == "text"), None)
        if not text_block or not text_block.text.strip():
            raise ValueError("Empty response from filter model")
        return json.loads(text_block.text)
    except Exception as e:
        print(f"[filter] WARNING: relevance filtering failed ({e}), falling back to raw Tavily answers", file=sys.stderr)
        return {
            "overview": raw_data.get("overview", {}).get("answer") or "No overview available.",
            "news": raw_data.get("news", {}).get("answer") or "No recent news found.",
            "tech_stack": raw_data.get("tech_stack", {}).get("answer") or "No tech stack signals found.",
            "leadership_funding": raw_data.get("leadership_funding", {}).get("answer") or "No leadership/funding data found.",
            "ai_devtools": raw_data.get("ai_devtools", {}).get("answer") or "No AI/devtools signals found.",
            "ai_vision": raw_data.get("ai_vision", {}).get("answer") or "No AI vision/transformation signals found.",
            "hiring_intent": raw_data.get("hiring_intent", {}).get("answer") or "No hiring intent signals found.",
            "competitor_tooling": raw_data.get("competitor_tooling", {}).get("answer") or "No competitor tooling signals found.",
            "engineering_pain": raw_data.get("engineering_pain", {}).get("answer") or "No engineering pain signals found.",
        }
