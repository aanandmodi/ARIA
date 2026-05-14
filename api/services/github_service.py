"""
GitHub service — PRs, issues, notifications, digest via PyGithub.
"""

from __future__ import annotations

import asyncio
from functools import partial

from github import Github

from api.core.config import settings
from api.core.logging import log

_github: Github | None = None


def _get_github() -> Github | None:
    global _github
    if not settings.github_token:
        return None
    if _github is None:
        _github = Github(settings.github_token)
    return _github


async def get_digest() -> str:
    """
    Build a brief GitHub digest for all configured repos:
    open PRs, open issues, failed CI.
    """
    gh = _get_github()
    if gh is None or not settings.github_repo_list:
        return ""
    try:
        loop = asyncio.get_event_loop()
        lines: list[str] = []

        for repo_name in settings.github_repo_list:
            try:
                repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))

                # Open PRs
                prs = await loop.run_in_executor(
                    None, partial(repo.get_pulls, state="open")
                )
                pr_list = list(prs[:5])
                if pr_list:
                    lines.append(f"📦 {repo_name} — {len(pr_list)} open PR(s):")
                    for pr in pr_list:
                        lines.append(f"  • #{pr.number} {pr.title} by {pr.user.login}")

                # Open issues assigned to user
                if settings.github_username:
                    issues = await loop.run_in_executor(
                        None,
                        partial(
                            repo.get_issues,
                            state="open",
                            assignee=settings.github_username,
                        ),
                    )
                    issue_list = list(issues[:5])
                    if issue_list:
                        lines.append(f"🐛 {repo_name} — {len(issue_list)} issue(s) assigned:")
                        for issue in issue_list:
                            lines.append(f"  • #{issue.number} {issue.title}")
            except Exception as exc:
                log.warning("github_repo_error", repo=repo_name, error=str(exc))
                continue

        return "\n".join(lines) if lines else "No GitHub updates."
    except Exception as exc:
        log.error("github_digest_failed", error=str(exc))
        return "GitHub digest unavailable."


async def get_notifications() -> list[dict]:
    """Get unread GitHub notifications."""
    gh = _get_github()
    if gh is None:
        return []
    try:
        loop = asyncio.get_event_loop()
        notifications = await loop.run_in_executor(
            None, partial(gh.get_user().get_notifications)
        )
        result = []
        for n in list(notifications[:10]):
            result.append({
                "title": n.subject.title,
                "type": n.subject.type,
                "repo": n.repository.full_name,
                "reason": n.reason,
                "url": n.subject.url,
            })
        return result
    except Exception as exc:
        log.error("github_notifications_failed", error=str(exc))
        return []
