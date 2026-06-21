# gtm-presales-mcp

## What this is

An MCP (Model Context Protocol) server that supports the pre-sales workflow of a 
Staff Solutions Engineer (enterprise sales engineering, not just demos — 
discovery-led, MEDDICC-style, business-outcome driven). The goal is to remove 
manual grunt work from account research, call prep, transcript processing, and 
deal tracking, so the SE can spend more time on judgment calls and customer 
conversations rather than admin.

This is a personal productivity tool, built and run locally on a Mac (Mac Mini 
M4 for ongoing dev, currently scaffolding on a MacBook). It is NOT a product to 
be shipped or sold — it's internal tooling for one user's own sales-engineering 
workflow at Stack Overflow (Stack Internal team).

It will eventually be exposed as MCP tools so any MCP-compatible client (Claude 
Desktop, Cursor, Claude Code) can call into it directly during work sessions — 
e.g. "research Acme Corp" or "pull MEDDIC from this transcript" as natural tool 
calls, not separate scripts to run.

## Architecture: four stages, built in this order

### Stage 1 — Account research (BUILD FIRST)
Given a company name or domain, pull together a research brief: company 
background, recent news, funding/leadership signals, tech stack hints, and 
anything relevant to an enterprise dev-tools / AI-in-the-SDLC sales motion. 
Likely uses web search APIs and/or scraping, normalized into a consistent 
output schema (not just dumped raw text) so later stages (deal tracker, call 
prep) can consume it programmatically.

### Stage 2 — RAG pipeline
Ingest internal knowledge (product docs, case studies, competitive intel, past 
deal notes) into a local vector store. Used to ground answers to questions like 
"how does Stack Internal handle data residency" or "what's our differentiation 
vs [competitor]" in real source material rather than hallucination. Local-first 
(Mac Mini has Ollama running already — Llama 3.2 and Mistral on Metal GPU) so 
this can run without hitting external APIs for every query if desired.

### Stage 3 — Transcript MEDDIC extraction
Take a raw call transcript (discovery call, demo, exec conversation) and extract 
structured MEDDIC fields: Metrics, Economic Buyer, Decision Criteria, Decision 
Process, Identify Pain, Champion (and Competition, if using MEDDICC). Output 
should be structured data, not prose — designed to feed directly into Stage 4 
(deal tracker) or a CRM-style record.

### Stage 4 — Notion-backed deal tracker
Takes outputs from stages 1–3 and writes/updates structured deal records in 
Notion via the Notion API/MCP integration. This becomes the system of record 
for account research + MEDDIC state per deal, so nothing extracted in stages 
1–3 dies in a chat conversation — it lands somewhere persistent and queryable.

## Tech stack / conventions
- Python 3.12, managed with `uv` (not pip/poetry/conda)
- FastMCP for the MCP server framework
- Local-first where possible: Ollama for LLM calls that don't need frontier 
  model quality, with the option to call out to Claude/OpenAI APIs for 
  higher-stakes extraction (e.g. MEDDIC parsing probably wants a stronger model 
  than local Llama 3.2)
- Output schemas should be structured (Pydantic models / JSON schema), not 
  freeform text, since outputs feed into later stages
- This builds on top of an existing `knowledge-mcp` project 
  (github.com/nickcole1001/knowledge-mcp) which already has Stack Internal mock 
  tools + a live GitHub API integration — gtm-presales-mcp is a separate, 
  parallel project, not a replacement

## What "done" looks like for Stage 1 (current focus)
An MCP tool — something like `research_account(company_name_or_domain: str)` — 
that returns a structured research brief object, callable from Claude Desktop 
or Claude Code, tested against at least 2–3 real prospect companies before 
moving to Stage 2.

## Explicitly out of scope (for now)
- Multi-user support / auth — this is single-user, local-only
- A UI — interaction is via MCP tool calls from existing AI clients, not a 
  custom frontend
- Production deployment / hosting — runs locally on Nick's machine(s) only
