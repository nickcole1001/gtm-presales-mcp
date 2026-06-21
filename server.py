from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP
from tools.research import research_account as _research_account
from tools.analyser import analyse_brief
from tools.github_researcher import research_github_org
from tools.notion_writer import save_brief_to_notion

mcp = FastMCP("gtm-presales-mcp")


@mcp.tool()
async def research_account(
    company_name: str,
    domain: str | None = None,
    github_org: str | None = None,
    save_to_notion: bool = True,
    analyse: bool = True,
) -> dict:
    """
    Research a prospect company for pre-sales preparation.

    Runs parallel searches and returns a structured brief covering:
    - Company overview and what they do
    - Recent news and announcements
    - Tech stack and engineering signals
    - Leadership team, funding, and valuation
    - Relevance to AI/devtools and developer productivity motion

    Optionally enriches with live GitHub org data (repo count, top languages,
    public member count, top repos by stars).

    When analyse=True (default), adds an SE analysis section interpreting all
    research signals through a Stack Internal lens with discovery questions.

    Saves the brief as a Notion page under GTM Presales MCP by default.

    Args:
        company_name: Prospect company name, e.g. "HSBC" or "Barclays"
        domain: Optional domain to disambiguate, e.g. "hsbc.com"
        github_org: GitHub organisation slug, e.g. "barclays" or "hsbc"
        save_to_notion: Whether to save the brief to Notion (default True)
        analyse: Whether to run SE analysis via Claude (default True)
    """
    brief = await _research_account(company_name, domain)

    if github_org:
        brief.github_profile = await research_github_org(github_org)

    if analyse:
        brief.se_analysis = await analyse_brief(brief)

    result = brief.model_dump()

    if save_to_notion:
        notion_url = await save_brief_to_notion(brief)
        result["notion_url"] = notion_url

    return result


if __name__ == "__main__":
    mcp.run()
