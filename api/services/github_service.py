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


async def _get_monitored_repos(gh: Github) -> list[str]:
    """Get the list of repositories to monitor (explicit list or all user repos)."""
    configured = settings.github_repo_list
    if not configured or configured == ["all"]:
        try:
            loop = asyncio.get_event_loop()
            repos = await loop.run_in_executor(None, partial(gh.get_user().get_repos))
            return [r.full_name for r in repos]
        except Exception as exc:
            log.error("github_auto_discovery_failed", error=str(exc))
            return []
    return configured


async def get_digest() -> str:
    """
    Build a brief GitHub digest for all configured/discovered repos:
    open PRs, open issues, failed CI.
    """
    gh = _get_github()
    if gh is None:
        return ""
    try:
        repos_to_check = await _get_monitored_repos(gh)
        if not repos_to_check:
            return "No GitHub repositories found."

        loop = asyncio.get_event_loop()
        lines: list[str] = []

        for repo_name in repos_to_check:
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
        count = 0
        for n in notifications:
            if count >= 10:
                break
            result.append({
                "title": n.subject.title,
                "type": n.subject.type,
                "repo": n.repository.full_name,
                "reason": n.reason,
                "url": n.subject.url,
            })
            count += 1
        return result
    except Exception as exc:
        log.error("github_notifications_failed", error=str(exc))
        return []


async def merge_pr(repo_name: str, pr_number: int, commit_message: str = "") -> bool:
    """Merge a GitHub PR."""
    gh = _get_github()
    if gh is None: return False
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        pr = await loop.run_in_executor(None, partial(repo.get_pull, pr_number))
        await loop.run_in_executor(None, partial(pr.merge, commit_message=commit_message))
        return True
    except Exception as exc:
        log.error("github_merge_pr_failed", error=str(exc), repo=repo_name, pr=pr_number)
        return False

async def close_issue(repo_name: str, issue_number: int) -> bool:
    """Close a GitHub Issue or PR."""
    gh = _get_github()
    if gh is None: return False
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        issue = await loop.run_in_executor(None, partial(repo.get_issue, issue_number))
        await loop.run_in_executor(None, partial(issue.edit, state="closed"))
        return True
    except Exception as exc:
        log.error("github_close_issue_failed", error=str(exc), repo=repo_name, issue=issue_number)
        return False

async def create_issue(repo_name: str, title: str, body: str = "") -> str | None:
    """Create a new GitHub issue."""
    gh = _get_github()
    if gh is None: return None
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        issue = await loop.run_in_executor(None, partial(repo.create_issue, title=title, body=body))
        return issue.html_url
    except Exception as exc:
        log.error("github_create_issue_failed", error=str(exc), repo=repo_name)
        return None

async def comment_issue(repo_name: str, issue_number: int, body: str) -> bool:
    """Comment on a GitHub issue or PR."""
    gh = _get_github()
    if gh is None: return False
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        issue = await loop.run_in_executor(None, partial(repo.get_issue, issue_number))
        await loop.run_in_executor(None, partial(issue.create_comment, body))
        return True
    except Exception as exc:
        log.error("github_comment_issue_failed", error=str(exc), repo=repo_name, issue=issue_number)
        return False


async def create_pull_request(
    repo_name: str,
    title: str,
    head: str,
    base: str = "main",
    body: str = ""
) -> str | None:
    """Create a new pull request."""
    gh = _get_github()
    if gh is None:
        return None
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        pr = await loop.run_in_executor(
            None,
            partial(repo.create_pull, title=title, body=body, head=head, base=base)
        )
        log.info("github_pr_created", repo=repo_name, pr_number=pr.number)
        return pr.html_url
    except Exception as exc:
        log.error("github_create_pr_failed", error=str(exc), repo=repo_name)
        return None


async def search_code(
    query: str,
    repo: str | None = None,
    limit: int = 10
) -> list[dict]:
    """Search code across repositories."""
    gh = _get_github()
    if gh is None:
        return []
    try:
        loop = asyncio.get_event_loop()
        
        # Build search query
        search_query = query
        if repo:
            search_query = f"{query} repo:{repo}"
        
        results = await loop.run_in_executor(
            None,
            partial(gh.search_code, search_query)
        )
        
        code_results = []
        for item in list(results[:limit]):
            code_results.append({
                "name": item.name,
                "path": item.path,
                "repo": item.repository.full_name,
                "url": item.html_url,
                "score": item.score
            })
        
        log.info("github_code_search_complete", query=query, results=len(code_results))
        return code_results
    except Exception as exc:
        log.error("github_code_search_failed", error=str(exc), query=query)
        return []


async def trigger_workflow(
    repo_name: str,
    workflow_id: str,
    ref: str = "main",
    inputs: dict | None = None
) -> bool:
    """Trigger a GitHub Actions workflow."""
    gh = _get_github()
    if gh is None:
        return False
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        workflow = await loop.run_in_executor(
            None,
            partial(repo.get_workflow, workflow_id)
        )
        
        await loop.run_in_executor(
            None,
            partial(workflow.create_dispatch, ref=ref, inputs=inputs or {})
        )
        
        log.info("github_workflow_triggered", repo=repo_name, workflow=workflow_id)
        return True
    except Exception as exc:
        log.error("github_trigger_workflow_failed", error=str(exc), repo=repo_name)
        return False


async def get_commit_history(
    repo_name: str,
    branch: str = "main",
    limit: int = 10
) -> list[dict]:
    """Get recent commit history."""
    gh = _get_github()
    if gh is None:
        return []
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        commits = await loop.run_in_executor(
            None,
            partial(repo.get_commits, sha=branch)
        )
        
        commit_list = []
        for commit in list(commits[:limit]):
            commit_list.append({
                "sha": commit.sha[:7],
                "message": commit.commit.message.split('\n')[0],
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "url": commit.html_url
            })
        
        log.info("github_commits_fetched", repo=repo_name, count=len(commit_list))
        return commit_list
    except Exception as exc:
        log.error("github_commits_failed", error=str(exc), repo=repo_name)
        return []


async def get_repository_info(repo_name: str) -> dict | None:
    """Get repository information."""
    gh = _get_github()
    if gh is None:
        return None
    try:
        loop = asyncio.get_event_loop()
        repo = await loop.run_in_executor(None, partial(gh.get_repo, repo_name))
        
        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "language": repo.language,
            "url": repo.html_url,
            "default_branch": repo.default_branch
        }
    except Exception as exc:
        log.error("github_repo_info_failed", error=str(exc), repo=repo_name)
        return None
