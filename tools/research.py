import asyncio
import os
import re
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from tavily import AsyncTavilyClient

load_dotenv()

from schemas.account import AccountResearchBrief, NewsItem
from tools.filter import filter_research

_BOILERPLATE = re.compile(
    r'share\s+(this\s+)?(page|article|post|story)\s*(on|via|with)?\s*(facebook|twitter|x|linkedin|email|whatsapp)?'
    r'|follow\s+us\s+on\s+(twitter|facebook|linkedin|instagram)'
    r'|subscribe\s+to\s+(our\s+)?(newsletter|updates)'
    r'|cookie\s+(policy|notice|settings)',
    re.IGNORECASE,
)


def _clean_snippet(text: str) -> str:
    text = _BOILERPLATE.sub('', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()[:300]


async def research_account(company_name: str, domain: str | None = None) -> AccountResearchBrief:
    client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    name_ref = f"{company_name} {domain}" if domain else company_name

    queries = {
        "overview": f"{name_ref} company overview what they do products services industry",
        "news": f"{name_ref} news announcements 2025",
        "tech_stack": f"{name_ref} technology stack engineering developer tools infrastructure",
        "leadership_funding": f"{name_ref} leadership team CEO CTO funding investors valuation",
        "ai_devtools": f"{name_ref} developer productivity AI software development engineering",
        "ai_vision": f"{name_ref} AI strategy AI transformation CEO CTO statement press release earnings call",
        "hiring_intent": f"{name_ref} hiring jobs developer experience platform engineering internal tools engineering productivity knowledge management",
        "competitor_tooling": f"{name_ref} Confluence Notion Guru internal wiki developer portal knowledge management tooling documentation platform",
        "engineering_pain": f"{name_ref} engineering blog developer experience onboarding documentation knowledge sharing technical debt",
    }

    keys = list(queries.keys())
    results = await asyncio.gather(*[
        client.search(
            query=queries[key],
            include_answer=True,
            search_depth="advanced",
            max_results=5,
        )
        for key in keys
    ])
    data = dict(zip(keys, results))

    print(f"[research] Tavily searches complete, running relevance filter for {company_name}...", file=sys.stderr)
    filtered = await filter_research(company_name, domain, data)

    news_items = [
        NewsItem(
            title=r["title"],
            url=r["url"],
            snippet=_clean_snippet(r.get("content", "")),
            published_date=r.get("published_date"),
        )
        for r in data["news"].get("results", [])
        if company_name.lower() in (r.get("title", "") + r.get("content", "")).lower()
           or (domain and domain.lower() in r.get("url", "").lower())
    ]

    seen: set[str] = set()
    all_sources: list[str] = []
    for key in keys:
        for r in data[key].get("results", []):
            url = r["url"]
            if url not in seen:
                seen.add(url)
                all_sources.append(url)

    return AccountResearchBrief(
        company_name=company_name,
        domain=domain,
        researched_at=datetime.now(timezone.utc).isoformat(),
        overview=filtered.get("overview") or "No overview available.",
        recent_news_summary=filtered.get("news") or "No recent news found.",
        recent_news=news_items,
        tech_stack_summary=filtered.get("tech_stack") or "No tech stack signals found.",
        leadership_and_funding_summary=filtered.get("leadership_funding") or "No leadership/funding data found.",
        ai_devtools_relevance=filtered.get("ai_devtools") or "No AI/devtools signals found.",
        ai_vision_and_transformation=filtered.get("ai_vision") or "No AI vision/transformation signals found.",
        hiring_intent=filtered.get("hiring_intent") or "No hiring intent signals found.",
        competitor_tooling=filtered.get("competitor_tooling") or "No competitor tooling signals found.",
        engineering_pain=filtered.get("engineering_pain") or "No engineering pain signals found.",
        sources=all_sources,
    )
