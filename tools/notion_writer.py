import os

from dotenv import load_dotenv
from notion_client import AsyncClient

from schemas.account import AccountResearchBrief

load_dotenv()


def _h2(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _p(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


async def save_brief_to_notion(brief: AccountResearchBrief) -> str:
    """Creates a Notion page for the account brief. Returns the new page URL."""
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN not set in .env")

    parent_page_id = os.environ.get("NOTION_PARENT_PAGE_ID")
    if not parent_page_id:
        raise ValueError("NOTION_PARENT_PAGE_ID not set in .env")

    client = AsyncClient(auth=token)

    blocks = [
        _h2("Overview"),
        _p(brief.overview),
        _h2("Recent News"),
        _p(brief.recent_news_summary),
        *[_bullet(f"{item.title} — {item.snippet}") for item in brief.recent_news],
        _h2("Tech Stack"),
        _p(brief.tech_stack_summary),
        _h2("Leadership & Funding"),
        _p(brief.leadership_and_funding_summary),
        _h2("AI & DevTools Relevance"),
        _p(brief.ai_devtools_relevance),
        _h2("AI Vision & Transformation"),
        _p(brief.ai_vision_and_transformation),
        _h2("Hiring Intent"),
        _p(brief.hiring_intent),
        _h2("Current Tooling & Competitor Signals"),
        _p(brief.competitor_tooling),
        _h2("Engineering Pain Signals"),
        _p(brief.engineering_pain),
        _h2("Sources"),
        *[_bullet(url) for url in brief.sources],
    ]

    if brief.github_profile:
        g = brief.github_profile
        langs = ", ".join(g.top_languages) if g.top_languages else "Unknown"
        blocks += [
            _h2("GitHub Organisation"),
            _p(f"Org: {g.org_name}  |  Public repos: {g.public_repos}  |  Public members: {g.public_members}"),
            _p(f"Top languages: {langs}"),
        ]
        if g.description:
            blocks.append(_p(g.description))
        if g.location or g.blog:
            meta = " | ".join(filter(None, [g.location, g.blog]))
            blocks.append(_p(meta))
        blocks.append(_p("Top repositories by stars:"))
        for repo in g.top_repos:
            desc = f" — {repo.description}" if repo.description else ""
            lang = f" [{repo.language}]" if repo.language else ""
            blocks.append(_bullet(f"{repo.name}{lang} ★{repo.stars}{desc}"))

    if brief.se_analysis:
        a = brief.se_analysis
        blocks += [
            _h2("SE Analysis (Stack Internal)"),
            _p("AI & Developer Tooling Signals"),
            _p(a.ai_devtools_signals),
            _p("Engineering Org Signals"),
            _p(a.engineering_org_signals),
            _p("Knowledge Management Pain"),
            _p(a.knowledge_management_pain),
            _p("Stack Internal Opportunity"),
            _p(a.stack_internal_opportunity),
            _p("Why Change / Why Now"),
            _p(a.why_change_why_now),
            _p("Discovery Questions"),
            *[_bullet(q) for q in a.discovery_questions],
        ]

    response = await client.pages.create(
        parent={"page_id": parent_page_id},
        properties={"title": {"title": [{"text": {"content": brief.company_name}}]}},
        children=blocks,
    )

    page_id = response["id"].replace("-", "")
    return f"https://notion.so/{page_id}"
