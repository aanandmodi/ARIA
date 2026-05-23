"""
GitHub handler — handles all PR, commit, issue, and repository operations.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service, github_service
from api.core.config import settings
from api.core.logging import log

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    action = params.get("action", "digest")
    repo = params.get("repo")
    number = params.get("number")
    text = params.get("text", "")

    if repo:
        # Strip trailing conversational suffixes like " repo", " repos", " repository", " github"
        for suffix in (" repo", " repos", " repository", " github"):
            if repo.lower().endswith(suffix):
                repo = repo[:-len(suffix)].strip()

    # Expand repo if username is set (e.g. "ARIA" -> "Aanandmodi/ARIA")
    if repo and "/" not in repo and settings.github_username:
        repo = f"{settings.github_username}/{repo}"
    
    # Fallback to default configured repo if none provided
    if not repo and settings.github_repo_list:
        repo = settings.github_repo_list[0]

    if action in ("prs", "pulls", "digest"):
        # Fetch PRs and issues digest or specifically open PRs
        await telegram_service.send_message("🔍 Fetching open Pull Requests and Issues...")
        digest = await github_service.get_digest()
        if not digest or digest == "No GitHub updates.":
            await telegram_service.send_message("✅ No open Pull Requests or Issues found in your monitored repositories.")
        else:
            await telegram_service.send_message(f"📦 <b>GitHub Status Digest:</b>\n\n{digest}")

    elif action in ("commits", "commit"):
        if not repo:
            await telegram_service.send_message("❌ Please specify a repository name to check commits.")
            return
            
        await telegram_service.send_message(f"🔍 Fetching recent commits for <b>{repo}</b>...")
        commits = await github_service.get_commit_history(repo, limit=5)
        if not commits:
            await telegram_service.send_message(f"❌ Failed to fetch commits or no commits found for <b>{repo}</b>.")
        else:
            lines = [f"<b>Recent Commits in {repo}:</b>\n"]
            for c in commits:
                lines.append(f"• <code>{c['sha']}</code> {c['message']} (by {c['author']})")
            await telegram_service.send_message("\n".join(lines))

    elif action == "review":
        if not repo or not number:
            await telegram_service.send_message("❌ Please specify both a repository name and PR number to review (e.g., 'review PR #5 in ARIA').")
            return
            
        try:
            pr_num = int(number)
        except ValueError:
            await telegram_service.send_message("❌ Invalid PR number.")
            return

        await telegram_service.send_message(f"🧠 Generating senior AI code review for PR #{pr_num} in <b>{repo}</b>...")
        review_text = await github_service.review_pr(repo, pr_num)
        
        msg = (
            f"🐙 <b>AI Code Review — PR #{pr_num} in {repo}</b>\n\n"
            f"{review_text}"
        )
        await telegram_service.send_message(msg)

    elif action == "merge":
        if not repo or not number:
            await telegram_service.send_message("❌ Please specify both a repository name and PR number to merge (e.g., 'merge PR #5 in ARIA').")
            return
            
        try:
            pr_num = int(number)
        except ValueError:
            await telegram_service.send_message("❌ Invalid Pull Request number.")
            return

        await telegram_service.send_message(f"⚙️ Merging PR #{pr_num} in <b>{repo}</b>...")
        success = await github_service.merge_pr(repo, pr_num, commit_message=text or "Merged by ARIA Personal Assistant")
        if success:
            await telegram_service.send_message(f"✅ Pull Request #{pr_num} in <b>{repo}</b> has been successfully merged!")
        else:
            await telegram_service.send_message(f"❌ Failed to merge PR #{pr_num} in <b>{repo}</b>. Check if there are conflicts or merge permissions.")

    elif action == "close":
        if not repo or not number:
            await telegram_service.send_message("❌ Please specify both a repository name and Issue/PR number to close.")
            return
            
        try:
            num = int(number)
        except ValueError:
            await telegram_service.send_message("❌ Invalid Issue/PR number.")
            return

        await telegram_service.send_message(f"⚙️ Closing Issue/PR #{num} in <b>{repo}</b>...")
        success = await github_service.close_issue(repo, num)
        if success:
            await telegram_service.send_message(f"✅ Issue/PR #{num} in <b>{repo}</b> has been closed!")
        else:
            await telegram_service.send_message(f"❌ Failed to close Issue/PR #{num} in <b>{repo}</b>.")

    elif action in ("comment", "reply_issue"):
        if not repo or not number or not text:
            await telegram_service.send_message("❌ Please specify repository, issue/PR number, and your comment text.")
            return
            
        try:
            num = int(number)
        except ValueError:
            await telegram_service.send_message("❌ Invalid Issue/PR number.")
            return

        await telegram_service.send_message(f"💬 Posting comment to PR/Issue #{num} in <b>{repo}</b>...")
        success = await github_service.comment_issue(repo, num, text)
        if success:
            await telegram_service.send_message(f"✅ Comment posted successfully to PR/Issue #{num} in <b>{repo}</b>!")
        else:
            await telegram_service.send_message(f"❌ Failed to post comment.")

    elif action == "create_issue":
        if not repo or not text:
            await telegram_service.send_message("❌ Please specify a repository and the issue title/description.")
            return
            
        title = text.split("\n")[0]
        body = "\n".join(text.split("\n")[1:]) if "\n" in text else ""
        
        await telegram_service.send_message(f"⚙️ Creating new issue in <b>{repo}</b>...")
        url = await github_service.create_issue(repo, title, body)
        if url:
            await telegram_service.send_message(f"✅ Issue created successfully!\n\n🔗 <a href='{url}'>{title}</a>")
        else:
            await telegram_service.send_message(f"❌ Failed to create issue in <b>{repo}</b>.")

    else:
        # Default fallback: get repository summary
        if repo:
            info = await github_service.get_repository_info(repo)
            if info:
                msg = (
                    f"📂 <b>Repository: {info['full_name']}</b>\n"
                    f"📝 <i>{info['description'] or 'No description'}</i>\n\n"
                    f"⭐ Stars: {info['stars']} | 🍴 Forks: {info['forks']}\n"
                    f"🐛 Open Issues: {info['open_issues']}\n"
                    f"🌐 Primary Language: {info['language']}\n"
                    f"🔗 <a href='{info['url']}'>View on GitHub</a>"
                )
                await telegram_service.send_message(msg)
                return
        await telegram_service.send_message("❓ Unsupported GitHub action requested.")
