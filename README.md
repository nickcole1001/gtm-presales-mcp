# gtm-presales-mcp

A local [Model Context Protocol](https://modelcontextprotocol.io) server for SE pre-sales workflows at Stack Overflow (Stack Internal). Runs inside Claude Desktop and surfaces structured, AI-enriched account research with one natural-language prompt.

## What it does

Given a company name, the `research_account` tool:

1. Fires **9 parallel Tavily searches** across: company overview, recent news, tech stack, leadership & funding, AI/devtools signals, AI vision & transformation, hiring intent, competitor tooling, and engineering pain
2. Passes all raw results through a **Claude Haiku relevance filter** — strips generic noise and boilerplate, keeps only content that is specifically about the target company
3. Optionally enriches the brief with **live GitHub org data** (repos, languages, member count, top repos by stars)
4. Runs a **Claude Opus SE analysis** framed around the Stack Internal value proposition and MEDDICC methodology — surfaces discovery questions grounded in the actual research
5. Saves a structured **Notion page** under your configured parent page

### Output sections

| Section | Signal |
|---|---|
| Overview | What the company does, size, industry |
| Recent News | Filtered news and announcements |
| Tech Stack | Engineering tooling and infrastructure signals |
| Leadership & Funding | Exec team, funding rounds, valuation |
| AI & DevTools Relevance | Developer-tooling-level AI adoption signals |
| AI Vision & Transformation | Executive-level public AI strategy/commitment signals |
| Hiring Intent | Active job posts for DevEx / Platform / Internal Tools roles |
| Current Tooling & Competitor Signals | Confluence, Notion, Guru, internal wiki usage signals |
| Engineering Pain Signals | Engineering blog posts and public signals around knowledge/onboarding pain |
| GitHub Organisation | Repo count, public members, top languages, top repos by stars |
| SE Analysis (Stack Internal) | MEDDICC-framed analysis with discovery questions |

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Claude Desktop](https://claude.ai/download)

### Install

```bash
git clone <repo>
cd gtm-presales-mcp
uv sync
```

### Configure environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `NOTION_TOKEN` | Notion → Settings → Connections → Develop your own integrations |
| `NOTION_PARENT_PAGE_ID` | The ID from the URL of the Notion page you want briefs saved under |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens (read:org scope) |

### Connect to Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gtm-presales-mcp": {
      "command": "/path/to/gtm-presales-mcp/.venv/bin/python",
      "args": ["-m", "fastmcp", "run", "/path/to/gtm-presales-mcp/server.py"],
      "cwd": "/path/to/gtm-presales-mcp"
    }
  }
}
```

Restart Claude Desktop. You should see the hammer icon (tools available).

## Usage

In Claude Desktop, **name the tool explicitly** — otherwise Claude will use its own web search instead:

```
Use the research_account tool to research Barclays (domain: barclays.com, github_org: barclays)
```

```
Use the research_account tool to research HSBC (domain: hsbc.com, analyse: true, save_to_notion: true)
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `company_name` | string | required | Company name, e.g. `"Barclays"` |
| `domain` | string | optional | Domain to disambiguate, e.g. `"barclays.com"` |
| `github_org` | string | optional | GitHub org slug, e.g. `"barclays"` |
| `save_to_notion` | bool | `true` | Save brief as a Notion page |
| `analyse` | bool | `true` | Run Claude SE analysis |

## Project structure

```
server.py               # FastMCP entrypoint — tool definition
schemas/
  account.py            # Pydantic models (AccountResearchBrief, SEAnalysis, etc.)
tools/
  research.py           # Tavily search orchestration
  filter.py             # Haiku relevance filter
  analyser.py           # Claude Opus SE analysis (MEDDICC framing)
  github_researcher.py  # GitHub org enrichment
  notion_writer.py      # Notion page creation
```

## Stack

- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework
- [Tavily](https://tavily.com) — search API
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) — Haiku (filter) + Opus (analysis)
- [notion-client](https://github.com/ramnes/notion-sdk-py) — Notion page creation
- [httpx](https://www.python-httpx.org) — GitHub API calls
- [uv](https://docs.astral.sh/uv/) — package management

## Roadmap

- **Stage 2:** `research_contact` — LinkedIn/web enrichment for champion/EB identification
- **Stage 3:** Job posting API integration (Adzuna) for structured hiring intent data
- **Stage 4:** MEDDICC deal tracker — capture and update deal state in Notion
