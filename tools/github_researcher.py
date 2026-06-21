import os
from collections import Counter

import httpx
from dotenv import load_dotenv

from schemas.account import GitHubOrgProfile, GitHubRepo

load_dotenv()

_BASE = "https://api.github.com"


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def research_github_org(org: str) -> GitHubOrgProfile:
    async with httpx.AsyncClient(headers=_headers(), timeout=15) as client:
        org_resp = await client.get(f"{_BASE}/orgs/{org}")
        org_resp.raise_for_status()
        org_data = org_resp.json()

        repos_resp = await client.get(
            f"{_BASE}/orgs/{org}/repos",
            params={"sort": "stars", "direction": "desc", "per_page": 10, "type": "public"},
        )
        repos_resp.raise_for_status()
        repos_data = repos_resp.json()

    top_repos = [
        GitHubRepo(
            name=r["name"],
            description=r.get("description"),
            stars=r["stargazers_count"],
            language=r.get("language"),
            url=r["html_url"],
        )
        for r in repos_data
    ]

    lang_counts = Counter(r.language for r in top_repos if r.language)
    top_languages = [lang for lang, _ in lang_counts.most_common()]

    return GitHubOrgProfile(
        org_name=org_data["login"],
        github_url=org_data["html_url"],
        description=org_data.get("description") or None,
        public_repos=org_data.get("public_repos", 0),
        public_members=org_data.get("public_members_count", 0),
        top_languages=top_languages,
        top_repos=top_repos,
        blog=org_data.get("blog") or None,
        location=org_data.get("location") or None,
    )
