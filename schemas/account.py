from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: str | None = None


class GitHubRepo(BaseModel):
    name: str
    description: str | None = None
    stars: int
    language: str | None = None
    url: str


class GitHubOrgProfile(BaseModel):
    org_name: str
    github_url: str
    description: str | None = None
    public_repos: int
    public_members: int
    top_languages: list[str]
    top_repos: list[GitHubRepo]
    blog: str | None = None
    location: str | None = None


class SEAnalysis(BaseModel):
    ai_devtools_signals: str
    engineering_org_signals: str
    knowledge_management_pain: str
    stack_internal_opportunity: str
    why_change_why_now: str
    discovery_questions: list[str]


class AccountResearchBrief(BaseModel):
    company_name: str
    domain: str | None = None
    researched_at: str
    overview: str
    recent_news_summary: str
    recent_news: list[NewsItem]
    tech_stack_summary: str
    leadership_and_funding_summary: str
    ai_devtools_relevance: str
    ai_vision_and_transformation: str
    hiring_intent: str
    competitor_tooling: str
    engineering_pain: str
    sources: list[str]
    github_profile: GitHubOrgProfile | None = None
    se_analysis: SEAnalysis | None = None
