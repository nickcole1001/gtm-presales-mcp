import json
import os
import sys

import anthropic
from dotenv import load_dotenv

from schemas.account import AccountResearchBrief, SEAnalysis

load_dotenv()

_SYSTEM = """You are an expert pre-sales analyst supporting a Staff Solutions Engineer at Stack Overflow (Stack Internal team). Stack Internal is an enterprise knowledge management and developer Q&A platform that helps engineering organisations:
- Capture and surface institutional knowledge at scale
- Reduce repetitive interruptions across engineering teams
- Accelerate developer onboarding and time-to-productivity
- Integrate AI into the SDLC (AI-in-the-SDLC motion)
- Measure and improve developer productivity

Stack Internal's key differentiators:
- Private, secure knowledge base with enterprise access controls
- Integrates with developer tooling (IDE, Slack, Jira, GitHub, etc.)
- AI-powered search and answer synthesis over private knowledge
- Analytics to surface knowledge gaps and team health signals
- Used by engineering teams of 500–50,000+ developers

You use the MEDDICC sales methodology (Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion, Competition).

Respond ONLY with a valid JSON object — no markdown fences, no explanation, no preamble. Match this exact schema:
{
  "ai_devtools_signals": "<AI strategy, developer tooling investments, AI coding assistant usage signals>",
  "engineering_org_signals": "<org size estimates, structure, growth signals, visible pain from hiring/job posts/tech decisions>",
  "knowledge_management_pain": "<institutional knowledge loss, onboarding friction, documentation debt, repeated-question signals — also check engineering blog pain signals and any public complaints from engineers>",
  "stack_internal_opportunity": "<specific business case for Stack Internal at this account — what MEDDICC pain does it solve, referencing current tooling gaps (e.g. Confluence dissatisfaction, lack of developer portal) and hiring signals that show active investment in this problem space>",
  "why_change_why_now": "<triggers creating urgency: recent news, funding, leadership hire, tech migration, regulatory pressure, PUBLIC commitments to AI strategy/transformation, OR active hiring for DevEx/Platform/Internal Tools roles (hiring = budget allocated = now)>",
  "discovery_questions": ["<5–7 sharp discovery questions grounded in the research, not generic>"]
}"""


def _github_section(brief: AccountResearchBrief) -> str:
    if not brief.github_profile:
        return ""
    g = brief.github_profile
    langs = ", ".join(g.top_languages) if g.top_languages else "unknown"
    top = "\n".join(
        f"  - {r.name} ({r.language or 'unknown'}) ★{r.stars}"
        + (f": {r.description}" if r.description else "")
        for r in g.top_repos[:5]
    )
    return f"""
**GitHub Organisation ({g.org_name}):**
Public repos: {g.public_repos} | Public members: {g.public_members}
Top languages: {langs}
Top repos:
{top}"""


def _user_message(brief: AccountResearchBrief) -> str:
    return f"""Analyse this prospect for Stack Internal pre-sales:

**Company:** {brief.company_name}{f" ({brief.domain})" if brief.domain else ""}

**Overview:**
{brief.overview}

**Recent News:**
{brief.recent_news_summary}

**Tech Stack:**
{brief.tech_stack_summary}

**Leadership & Funding:**
{brief.leadership_and_funding_summary}

**AI & DevTools Signals:**
{brief.ai_devtools_relevance}

**AI Vision & Transformation:**
{brief.ai_vision_and_transformation}

**Hiring Intent (DevEx / Platform / Internal Tools roles):**
{brief.hiring_intent}

**Current Tooling & Competitor Signals:**
{brief.competitor_tooling}

**Engineering Pain (blog posts / public signals):**
{brief.engineering_pain}{_github_section(brief)}"""


async def analyse_brief(brief: AccountResearchBrief) -> SEAnalysis:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set — add it to .env")

    client = anthropic.AsyncAnthropic(api_key=api_key)

    try:
        response = await client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=_SYSTEM,
            messages=[{"role": "user", "content": _user_message(brief)}],
        )
    except anthropic.APIError as e:
        print(f"[analyser] Anthropic API error ({type(e).__name__}): {e}", file=sys.stderr)
        raise

    text_block = next((b for b in response.content if b.type == "text"), None)
    if not text_block or not text_block.text.strip():
        print(f"[analyser] No text in response. stop_reason={response.stop_reason}, content types={[b.type for b in response.content]}", file=sys.stderr)
        raise ValueError("Empty or missing text block in Claude response")

    try:
        return SEAnalysis.model_validate(json.loads(text_block.text))
    except (json.JSONDecodeError, Exception) as e:
        print(f"[analyser] Parse error: {e}\nRaw text: {text_block.text[:500]}", file=sys.stderr)
        raise
